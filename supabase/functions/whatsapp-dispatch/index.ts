// Sends queued WhatsApp messages (public.whatsapp_messages, status 'queued').
// Called every 5 minutes by pg_cron (x-dispatch-secret header), or by the Super Admin.
// Deploy with "Enforce JWT verification" OFF; access is checked in the code below.
// Rules: quiet hours 9 AM–8 PM IST; client consent and stage re-checked at send time;
// at most 2 client messages per number per day; a template must be APPROVED by Meta
// (otherwise the message stays queued and is retried later).
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GRAPH = "https://graph.facebook.com/v24.0";
const WABA_ID = Deno.env.get("WHATSAPP_WABA_ID") || "927100876842881";
const PHONE_NUMBER_ID = Deno.env.get("WHATSAPP_PHONE_NUMBER_ID") || "1055145887685477";
const BATCH = 40;
const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-dispatch-secret" } });

function istNow() {
  const d = new Date(Date.now() + 5.5 * 3600e3);
  return { hour: d.getUTCHours(), date: d.toISOString().slice(0, 10) };
}
function nextNineAmIst(): string {
  const d = new Date(Date.now() + 5.5 * 3600e3);
  const nine = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + (d.getUTCHours() >= 9 ? 1 : 0), 9, 0) - 5.5 * 3600e3;
  return new Date(nine).toISOString();
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return json("ok");
  const url = Deno.env.get("SUPABASE_URL")!, service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, anon = Deno.env.get("SUPABASE_ANON_KEY")!;
  const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const db = createClient(url, service, { auth: { persistSession: false } });
  // The schedule (pg_cron) sends x-dispatch-secret; the Super Admin can also run it by hand.
  const dispatchSecret = Deno.env.get("WHATSAPP_DISPATCH_SECRET") || "";
  let allowed = jwt === service || (dispatchSecret.length >= 24 && req.headers.get("x-dispatch-secret") === dispatchSecret);
  if (!allowed && jwt) {
    const u = await createClient(url, anon, { global: { headers: { Authorization: `Bearer ${jwt}` } }, auth: { persistSession: false } }).auth.getUser(jwt);
    if (u.data?.user) {
      const { data: r } = await db.from("user_roles").select("role").eq("user_id", u.data.user.id).maybeSingle();
      allowed = r?.role === "super_admin";
    }
  }
  if (!allowed) return json({ error: "Not allowed" }, 403);

  const token = Deno.env.get("WHATSAPP_ACCESS_TOKEN");
  if (!token) return json({ error: "WHATSAPP_ACCESS_TOKEN not set" }, 503);

  const { hour, date } = istNow();
  if (hour < 9 || hour >= 20) return json({ ok: true, skipped: "quiet hours (9 AM–8 PM IST)" });

  // Which templates are approved right now?
  const tr = await fetch(`${GRAPH}/${WABA_ID}/message_templates?fields=name,status,language&limit=200`, { headers: { Authorization: `Bearer ${token}` } });
  const tj = await tr.json().catch(() => ({}));
  const approved = new Map<string, string>();
  for (const t of tj?.data ?? []) if (t.status === "APPROVED") approved.set(t.name, t.language);

  const { data: due } = await db.from("whatsapp_messages").select("*").eq("status", "queued").lte("scheduled_for", new Date().toISOString()).order("scheduled_for").limit(BATCH);
  const summary = { sent: 0, failed: 0, skipped: 0, waiting_template: 0, deferred: 0, stopped: "" };

  for (const m of due ?? []) {
    // A utility re-submission named <template>_u is used once Meta approves it (16 Nov 2026).
    const tpl = approved.has(m.template_name + "_u") ? m.template_name + "_u" : m.template_name;
    if (!approved.has(tpl)) { summary.waiting_template++; continue; }

    // Claim the row so two runs never send it twice.
    const { data: claimed } = await db.from("whatsapp_messages").update({ status: "sending", attempts: (m.attempts ?? 0) + 1 }).eq("id", m.id).eq("status", "queued").select("id");
    if (!claimed?.length) continue;

    if (m.recipient_kind === "client") {
      // A client message whose lead was deleted (lead_id now null) is never sent.
      const { data: lead } = m.lead_id ? await db.from("leads").select("whatsapp_opt_in,stage").eq("id", m.lead_id).maybeSingle() : { data: null };
      const goodbye = m.message_key === "C-nolead" && lead?.stage === "Clear no lead";
      if (!lead || !lead.whatsapp_opt_in || (!goodbye && ["False lead", "Clear no lead"].includes(lead.stage))) {
        await db.from("whatsapp_messages").update({ status: "skipped", error_detail: "No consent or not a lead at send time" }).eq("id", m.id);
        summary.skipped++; continue;
      }
      const { count } = await db.from("whatsapp_messages").select("id", { count: "exact", head: true })
        .eq("recipient_phone", m.recipient_phone).eq("recipient_kind", "client").in("status", ["sent", "delivered", "read"])
        .gte("sent_at", new Date(Date.parse(date + "T00:00:00+05:30")).toISOString());
      if ((count ?? 0) >= 2) {
        await db.from("whatsapp_messages").update({ status: "queued", scheduled_for: nextNineAmIst() }).eq("id", m.id);
        summary.deferred++; continue;
      }
    }

    const params: string[] = Array.isArray(m.params) ? m.params.map((p: unknown) => String(p ?? "-").slice(0, 900) || "-") : [];
    const payload = {
      messaging_product: "whatsapp", recipient_type: "individual", to: m.recipient_phone, type: "template",
      template: { name: tpl, language: { code: approved.get(tpl) || "en" },
        components: params.length ? [{ type: "body", parameters: params.map((text) => ({ type: "text", text })) }] : [] },
    };
    const r = await fetch(`${GRAPH}/${PHONE_NUMBER_ID}/messages`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const j = await r.json().catch(() => ({}));
    if (r.ok) {
      await db.from("whatsapp_messages").update({ status: "sent", wamid: j?.messages?.[0]?.id ?? null, sent_at: new Date().toISOString(), error_code: "", error_detail: "" }).eq("id", m.id);
      summary.sent++;
    } else {
      const code = String(j?.error?.code ?? r.status);
      // Number/account not ready, rate limit or Meta outage: put it back and stop this run.
      if (["133010", "131056", "130429", "131016", "2", "4"].includes(code) || r.status >= 500) {
        await db.from("whatsapp_messages").update({ status: "queued", error_code: code, error_detail: String(j?.error?.message ?? "").slice(0, 500) }).eq("id", m.id);
        summary.stopped = `${code}: ${j?.error?.message ?? ""}`; break;
      }
      await db.from("whatsapp_messages").update({ status: "failed", failed_at: new Date().toISOString(), error_code: code, error_detail: String(j?.error?.error_data?.details ?? j?.error?.message ?? "").slice(0, 500) }).eq("id", m.id);
      summary.failed++;
    }
  }
  return json({ ok: true, approved_templates: approved.size, due: due?.length ?? 0, ...summary });
});
