// LeadFlow CRM – WhatsApp via Meta Cloud API (no Twilio).
// Step 1 of the WhatsApp build: a read-only "discover" action that reports which
// WhatsApp Business Accounts and phone numbers the saved token can use.
// Secrets: WHATSAPP_ACCESS_TOKEN (system user token). Never returned or logged.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GRAPH = "https://graph.facebook.com/v24.0";
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });

async function graph(path: string, token: string) {
  const r = await fetch(`${GRAPH}/${path}`, { headers: { Authorization: `Bearer ${token}` } });
  const body = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, body };
}

// Only the Super Admin (signed in) or the service role (Supabase dashboard test) may call this.
async function authorised(req: Request): Promise<boolean> {
  const url = Deno.env.get("SUPABASE_URL")!, anon = Deno.env.get("SUPABASE_ANON_KEY")!, service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!jwt) return false;
  if (jwt === service) return true;
  const userClient = createClient(url, anon, { global: { headers: { Authorization: "Bearer " + jwt } }, auth: { persistSession: false } });
  const { data } = await userClient.auth.getUser(jwt);
  if (!data?.user) return false;
  const admin = createClient(url, service, { auth: { persistSession: false } });
  const { data: role } = await admin.from("user_roles").select("role").eq("user_id", data.user.id).maybeSingle();
  return role?.role === "super_admin";
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed." }, 405);
  try {
    if (!(await authorised(req))) return json({ error: "Only the Super Admin can use this." }, 403);
    const token = Deno.env.get("WHATSAPP_ACCESS_TOKEN");
    if (!token) return json({ error: "WHATSAPP_ACCESS_TOKEN is not set in Supabase Edge Function secrets." }, 503);
    const input = await req.json().catch(() => ({}));
    const action = input?.action || "discover";
    if (action !== "discover") return json({ error: "Unsupported action." }, 400);

    // Which WhatsApp Business Accounts was this token granted? (debug_token lists them per permission)
    const dbg = await graph(`debug_token?input_token=${encodeURIComponent(token)}`, token);
    if (!dbg.ok) return json({ ok: false, step: "debug_token", status: dbg.status, error: dbg.body?.error?.message || "Token check failed." }, 502);
    const d = dbg.body?.data || {};
    const scopes: Array<{ scope: string; target_ids?: string[] }> = d.granular_scopes || [];
    const wabaIds = [...new Set(scopes.filter((s) => s.scope.startsWith("whatsapp_business")).flatMap((s) => s.target_ids || []))];
    // Fallback: a token granted business-wide lists no target ids, so ask the business itself.
    const businessId = typeof input?.business_id === "string" && /^\d+$/.test(input.business_id) ? input.business_id : null;
    if (!wabaIds.length && businessId) {
      for (const edge of ["owned_whatsapp_business_accounts", "client_whatsapp_business_accounts"]) {
        const r = await graph(`${businessId}/${edge}?fields=id,name&limit=50`, token);
        if (r.ok) for (const w of r.body?.data || []) if (!wabaIds.includes(w.id)) wabaIds.push(w.id);
      }
    }

    const accounts = [];
    for (const id of wabaIds) {
      const waba = await graph(`${id}?fields=id,name`, token);
      const nums = await graph(`${id}/phone_numbers?fields=id,display_phone_number,verified_name,quality_rating,platform_type,code_verification_status,messaging_limit_tier`, token);
      accounts.push({ waba_id: id, name: waba.body?.name ?? null, phone_numbers: nums.ok ? nums.body?.data ?? [] : { error: nums.body?.error?.message } });
    }
    return json({
      ok: true,
      token: { valid: d.is_valid ?? null, app_id: d.app_id ?? null, expires_at: d.expires_at ?? null, scopes: scopes.map((s) => s.scope) },
      whatsapp_accounts: accounts,
    });
  } catch (e) {
    console.error("whatsapp-cloud failed", e instanceof Error ? e.message : e);
    return json({ error: "Unexpected server error." }, 500);
  }
});
