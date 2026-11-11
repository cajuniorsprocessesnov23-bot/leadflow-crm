import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });
}
Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed." }, 405);
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    const webhookUrl = Deno.env.get("N8N_WEBHOOK_URL");
    const webhookSecret = Deno.env.get("N8N_WEBHOOK_SECRET");
    if (!supabaseUrl || !anonKey || !serviceKey) return json({ error: "Server authentication is not configured." }, 500);
    const auth = req.headers.get("Authorization") || "";
    const jwt = auth.replace(/^Bearer\s+/i, "");
    if (!jwt) return json({ error: "Sign in to LeadFlow CRM first." }, 401);
    const userClient = createClient(supabaseUrl, anonKey, { global: { headers: { Authorization: "Bearer " + jwt } }, auth: { persistSession: false, autoRefreshToken: false } });
    const { data: userData, error: userError } = await userClient.auth.getUser(jwt);
    if (userError || !userData.user) return json({ error: "Your session is invalid or expired." }, 401);
    const adminClient = createClient(supabaseUrl, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } });
    const { data: roleRow, error: roleError } = await adminClient.from("user_roles").select("role,permissions").eq("user_id", userData.user.id).maybeSingle();
    if (roleError) return json({ error: "Could not verify CRM permissions." }, 500);
    if (!roleRow || !(["admin","super_admin"].includes(roleRow.role) || roleRow.permissions?.leads_create === true || roleRow.permissions?.leads_edit === true)) {
      return json({ error: "You do not have permission to dispatch CRM automation events." }, 403);
    }
    if (!webhookUrl || !webhookSecret) {
      return json({ ok: false, configured: false, message: "n8n is not connected yet. Configure N8N_WEBHOOK_URL and N8N_WEBHOOK_SECRET as Supabase Edge Function secrets." });
    }
    let input: { event?: unknown; payload?: unknown };
    try { input = await req.json(); } catch { return json({ error: "Request body must be valid JSON." }, 400); }
    const allowed = new Set(["lead.created","payment.confirmed","payment.reminder_due"]);
    if (typeof input.event !== "string" || !allowed.has(input.event)) return json({ error: "Unsupported automation event." }, 400);
    if (!input.payload || typeof input.payload !== "object" || Array.isArray(input.payload)) return json({ error: "Event payload is required." }, 400);
    const eventId = crypto.randomUUID();
    const eventBody = { eventId, event: input.event, occurredAt: new Date().toISOString(), source: "leadflow-crm", actor: { id: userData.user.id, email: userData.user.email }, payload: input.payload };
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-leadflow-secret": webhookSecret, "x-leadflow-event-id": eventId },
      body: JSON.stringify(eventBody),
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      console.error("n8n webhook returned", response.status, await response.text().catch(() => ""));
      return json({ ok: false, error: "n8n webhook returned HTTP " + response.status + "." }, 502);
    }
    return json({ ok: true, eventId, status: response.status });
  } catch (error) {
    console.error("n8n-dispatch failed", error);
    return json({ error: "Could not dispatch the automation event." }, 500);
  }
});
