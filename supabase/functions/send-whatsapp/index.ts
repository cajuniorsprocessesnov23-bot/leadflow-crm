import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function whatsappAddress(value: string) {
  const cleaned = value.trim().replace(/^whatsapp:/i, "");
  if (!/^\+[1-9]\d{7,14}$/.test(cleaned)) {
    throw new Error("Use an international phone number, e.g. +919876543210.");
  }
  return "whatsapp:" + cleaned;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed." }, 405);

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    const sid = Deno.env.get("TWILIO_ACCOUNT_SID");
    const token = Deno.env.get("TWILIO_AUTH_TOKEN");
    const fromRaw = Deno.env.get("TWILIO_WHATSAPP_FROM");

    if (!supabaseUrl || !anonKey || !serviceKey) {
      return json({ error: "Server authentication is not configured." }, 500);
    }
    if (!sid || !token || !fromRaw) {
      return json({
        error: "Twilio is not configured yet. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_FROM as Supabase Edge Function secrets.",
      }, 503);
    }

    const authHeader = req.headers.get("Authorization") || "";
    const jwt = authHeader.replace(/^Bearer\s+/i, "");
    if (!jwt) return json({ error: "Sign in to LeadFlow CRM first." }, 401);

    const userClient = createClient(supabaseUrl, anonKey, {
      global: { headers: { Authorization: "Bearer " + jwt } },
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: userData, error: userError } = await userClient.auth.getUser(jwt);
    if (userError || !userData.user) return json({ error: "Your session is invalid or expired." }, 401);

    const adminClient = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: roleRow, error: roleError } = await adminClient
      .from("user_roles").select("role").eq("user_id", userData.user.id).maybeSingle();
    if (roleError) return json({ error: "Could not verify CRM permissions." }, 500);
    if (!roleRow || !["admin", "super_admin"].includes(roleRow.role)) {
      return json({ error: "Only CRM Admin and Super Admin can send WhatsApp messages." }, 403);
    }

    let payload: { to?: unknown; body?: unknown };
    try { payload = await req.json(); } catch { return json({ error: "Request body must be valid JSON." }, 400); }
    if (typeof payload.to !== "string" || typeof payload.body !== "string") {
      return json({ error: "Recipient and message are required." }, 400);
    }
    const body = payload.body.trim();
    if (!body || body.length > 1500) return json({ error: "Message must contain 1–1500 characters." }, 400);

    let to: string, from: string;
    try {
      to = whatsappAddress(payload.to);
      from = whatsappAddress(fromRaw);
    } catch (e) {
      return json({ error: e instanceof Error ? e.message : "Invalid WhatsApp number." }, 400);
    }

    const form = new URLSearchParams({ To: to, From: from, Body: body });
    const twilioResponse = await fetch(
      `https://api.twilio.com/2010-04-01/Accounts/${encodeURIComponent(sid)}/Messages.json`,
      {
        method: "POST",
        headers: {
          "Authorization": "Basic " + btoa(sid + ":" + token),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: form.toString(),
      },
    );
    const result = await twilioResponse.json().catch(() => ({}));
    if (!twilioResponse.ok) {
      const message = typeof result?.message === "string" ? result.message : "Twilio rejected the message.";
      return json({ error: message, code: result?.code ?? null }, twilioResponse.status >= 500 ? 502 : 400);
    }
    return json({ success: true, sid: result.sid, status: result.status, to: result.to });
  } catch (error) {
    console.error("send-whatsapp failed", error);
    return json({ error: "Unexpected server error while sending WhatsApp message." }, 500);
  }
});
