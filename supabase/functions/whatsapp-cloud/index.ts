// LeadFlow CRM – WhatsApp via Meta Cloud API (no Twilio).
// Super Admin tools for the WhatsApp build: "discover" (which account/number the token
// can use), "templates" (approved templates) and "send_test" (one test message).
// Secrets: WHATSAPP_ACCESS_TOKEN (system user token). Never returned or logged.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GRAPH = "https://graph.facebook.com/v24.0";
// legal wegal, +91 93700 77727 (found with the discover action on 2026-11-13). Not secret.
// Override with Supabase secrets WHATSAPP_WABA_ID / WHATSAPP_PHONE_NUMBER_ID to switch numbers.
const WABA_ID = Deno.env.get("WHATSAPP_WABA_ID") || "927100876842881";
const PHONE_NUMBER_ID = Deno.env.get("WHATSAPP_PHONE_NUMBER_ID") || "1055145887685477";
const HI_TECH_BUSINESS_ID = "1256389646022701";
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

    // Approved message templates on the legal wegal WhatsApp account (read-only).
    if (action === "templates") {
      const t = await graph(`${WABA_ID}/message_templates?fields=name,status,category,language&limit=100`, token);
      if (!t.ok) return json({ ok: false, error: t.body?.error?.message || "Could not list templates." }, 502);
      return json({ ok: true, templates: t.body?.data ?? [] });
    }

    // Why might messages not be delivered? Meta's health status for the account and
    // number (can_send_message + reasons such as a missing payment method). Read-only.
    if (action === "diagnose") {
      const waba = await graph(`${WABA_ID}?fields=id,name,account_review_status,business_verification_status,health_status`, token);
      const phone = await graph(`${PHONE_NUMBER_ID}?fields=id,display_phone_number,status,name_status,account_mode,quality_rating,messaging_limit_tier,platform_type,code_verification_status,health_status`, token);
      const apps = await graph(`${WABA_ID}/subscribed_apps`, token);
      return json({ ok: true, waba: waba.ok ? waba.body : { error: waba.body?.error?.message }, phone: phone.ok ? phone.body : { error: phone.body?.error?.message }, subscribed_apps: apps.ok ? (apps.body?.data || []).map((a: { whatsapp_business_api_data?: { name?: string; id?: string } }) => a.whatsapp_business_api_data?.name || a.whatsapp_business_api_data?.id) : { error: apps.body?.error?.message } });
    }

    // All WhatsApp accounts and numbers this token can see in the Hi Tech portfolio (read-only).
    if (action === "list_numbers") {
      const f = "id,name,phone_numbers{id,display_phone_number,verified_name,status,platform_type,code_verification_status}";
      const own = await graph(`${HI_TECH_BUSINESS_ID}/owned_whatsapp_business_accounts?fields=${f}`, token);
      const cli = await graph(`${HI_TECH_BUSINESS_ID}/client_whatsapp_business_accounts?fields=${f}`, token);
      return json({ ok: true, in_use: { waba: WABA_ID, phone: PHONE_NUMBER_ID }, owned: own.ok ? own.body?.data : { error: own.body?.error?.message }, client: cli.ok ? cli.body?.data : { error: cli.body?.error?.message } });
    }

    // Submit a message template for Meta approval. body may use {{1}}, {{2}}…; give one
    // example value per variable in examples. buttons: up to 3 quick-reply texts.
    if (action === "create_template") {
      const name = String(input?.name || "");
      if (!/^[a-z0-9_]{1,512}$/.test(name)) return json({ error: "Template name: lowercase letters, numbers and _ only." }, 400);
      const category = ["UTILITY", "MARKETING", "AUTHENTICATION"].includes(input?.category) ? input.category : "UTILITY";
      const text = String(input?.body || "").trim();
      if (!text) return json({ error: "Give the body text." }, 400);
      const examples: string[] = Array.isArray(input?.examples) ? input.examples.map(String) : [];
      const components: Record<string, unknown>[] = [{ type: "BODY", text, ...(examples.length ? { example: { body_text: [examples] } } : {}) }];
      if (typeof input?.footer === "string" && input.footer.trim()) components.push({ type: "FOOTER", text: input.footer.trim().slice(0, 60) });
      const btns: string[] = Array.isArray(input?.buttons) ? input.buttons.map(String).slice(0, 3) : [];
      if (btns.length) components.push({ type: "BUTTONS", buttons: btns.map((t) => ({ type: "QUICK_REPLY", text: t.slice(0, 25) })) });
      const r = await fetch(`${GRAPH}/${WABA_ID}/message_templates`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ name, category, language: typeof input?.language === "string" ? input.language : "en", components }),
      });
      const body = await r.json().catch(() => ({}));
      return json({ ok: r.ok, result: r.ok ? body : null, error: body?.error?.error_user_msg || body?.error?.message || null }, r.ok ? 200 : 400);
    }

    // Subscribe this token's Meta app to the legal wegal WhatsApp account, so Meta sends
    // its message/status webhooks to the app's callback URL (our whatsapp-webhook function).
    if (action === "subscribe_app") {
      const r = await fetch(`${GRAPH}/${WABA_ID}/subscribed_apps`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) return json({ error: body?.error?.message || "Meta refused the subscription", code: body?.error?.code }, 400);
      const apps = await graph(`${WABA_ID}/subscribed_apps`, token);
      return json({ ok: true, result: body, subscribed_apps: (apps.body?.data || []).map((a: { whatsapp_business_api_data?: { name?: string; id?: string } }) => a.whatsapp_business_api_data || a) });
    }

    // Ask Meta to (re-)register +91 93700 77727 for Cloud API sending. Needs the number's
    // 6-digit two-step PIN (if none is set, this PIN becomes it). Returns Meta's answer as-is.
    if (action === "register") {
      const pin = String(input?.pin || "");
      if (!/^\d{6}$/.test(pin)) return json({ error: "Give a 6-digit PIN." }, 400);
      const r = await fetch(`${GRAPH}/${PHONE_NUMBER_ID}/register`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ messaging_product: "whatsapp", pin }),
      });
      const body = await r.json().catch(() => ({}));
      return json({ ok: r.ok, status: r.status, result: r.ok ? body : null, error: body?.error?.message ?? null, code: body?.error?.code ?? null, subcode: body?.error?.error_subcode ?? null, details: body?.error?.error_data?.details ?? null }, r.ok ? 200 : 502);
    }

    // One test message from +91 93700 77727 to a number the Super Admin types in.
    // template: an APPROVED template name (business-initiated); text: free-form, only
    // delivered if that person messaged the business in the last 24 hours.
    if (action === "send_test") {
      const to = String(input?.to || "").replace(/[^\d]/g, "");
      if (!/^[1-9]\d{9,14}$/.test(to)) return json({ error: "Give the number with country code, e.g. 919876543210." }, 400);
      let message: Record<string, unknown>;
      if (typeof input?.template === "string" && /^[a-z0-9_]{1,512}$/.test(input.template)) {
        const params: string[] = Array.isArray(input?.params) ? input.params.map((p: unknown) => String(p ?? "-").slice(0, 900) || "-") : [];
        message = { type: "template", template: { name: input.template, language: { code: typeof input?.language === "string" ? input.language : "en_US" },
          ...(params.length ? { components: [{ type: "body", parameters: params.map((text) => ({ type: "text", text })) }] } : {}) } };
      } else if (typeof input?.text === "string" && input.text.trim()) {
        message = { type: "text", text: { body: input.text.trim().slice(0, 1000) } };
      } else return json({ error: "Give either template or text." }, 400);
      const r = await fetch(`${GRAPH}/${PHONE_NUMBER_ID}/messages`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ messaging_product: "whatsapp", recipient_type: "individual", to, ...message }),
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) return json({ ok: false, status: r.status, error: body?.error?.message || "Meta rejected the message.", code: body?.error?.code ?? null, details: body?.error?.error_data?.details ?? null }, 502);
      return json({ ok: true, message_id: body?.messages?.[0]?.id ?? null, status: body?.messages?.[0]?.message_status ?? "accepted" });
    }

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
