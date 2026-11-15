// WhatsApp Cloud API webhook for Legal Wegal (+91 93700 77727).
// - GET: Meta's one-time verification (hub.verify_token must equal WHATSAPP_VERIFY_TOKEN).
// - POST: delivery statuses + client replies. Every POST must carry a valid
//   X-Hub-Signature-256 made with WHATSAPP_APP_SECRET, otherwise it is rejected.
// Deploy with "Enforce JWT verification" OFF (Meta cannot send a Supabase JWT).
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GRAPH = "https://graph.facebook.com/v24.0";
const PHONE_NUMBER_ID = Deno.env.get("WHATSAPP_PHONE_NUMBER_ID") || "1055145887685477";
const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });

// ---- Replies sent back to the client (inside the 24-hour window, so free text is allowed) ----
const TXT = {
  stop: "You will no longer get WhatsApp updates from Legal Wegal. Reply START anytime to turn them back on.",
  start: "WhatsApp updates from Legal Wegal are turned back on. Thank you!",
  slotIntro: "Sure! When should our team call you?",
  slotDone: (when: string) => `Thank you! Our team will call you ${when}.`,
  callNow: "Thank you! Our team will call you shortly.",
  offline: (day: string) => `Thank you! Our team is offline right now (working hours 9 AM to 8 PM). We will call you in the next working hours, from 9 AM ${day}.`,
  notInterested: "Thank you for letting us know. We won't message you about this again. If you need help in future, just message us here.",
  details: "Thank you! Our team will share the details with you here shortly.",
  paidAlready: "Thank you! Our team will check and confirm your payment shortly.",
  happy: "Thank you so much! We're glad we could help.",
};
// Callback slots offered after "Call later" (ids are stable; titles max 24 chars).
const SLOTS: { id: string; title: string; when: string; at: () => Date }[] = [
  { id: "slot_1h", title: "In 1 hour", when: "in about an hour", at: () => new Date(Date.now() + 3600e3) },
  { id: "slot_today_6pm", title: "Today, 6 PM", when: "today at 6 PM", at: () => ist(0, 18) },
  { id: "slot_tmrw_11am", title: "Tomorrow, 11 AM", when: "tomorrow at 11 AM", at: () => ist(1, 11) },
  { id: "slot_tmrw_4pm", title: "Tomorrow, 4 PM", when: "tomorrow at 4 PM", at: () => ist(1, 16) },
];
const EARLY_STAGES = (s: string) => s === "Unverified" || s === "Verified" || s.startsWith("Not picked");

// Date at a given IST hour, `days` days from today (IST).
function ist(days: number, hour: number): Date {
  const nowIst = new Date(Date.now() + 5.5 * 3600e3);
  const d = Date.UTC(nowIst.getUTCFullYear(), nowIst.getUTCMonth(), nowIst.getUTCDate() + days, hour, 0) - 5.5 * 3600e3;
  return new Date(Math.max(d, Date.now() + 15 * 60e3));
}
// Working hours for call-backs: 9 AM to 8 PM IST.
function offHours(d: Date): boolean {
  const h = new Date(d.getTime() + 5.5 * 3600e3).getUTCHours();
  return h < 9 || h >= 20;
}
function nextOpen(from = new Date()): { at: Date; day: string } {
  const ist0 = new Date(from.getTime() + 5.5 * 3600e3);
  const before9 = ist0.getUTCHours() < 9;
  const at = new Date(Date.UTC(ist0.getUTCFullYear(), ist0.getUTCMonth(), ist0.getUTCDate() + (before9 ? 0 : 1), 9, 0) - 5.5 * 3600e3);
  return { at, day: before9 ? "today" : "tomorrow" };
}
const last10 = (p: string) => String(p || "").replace(/\D/g, "").slice(-10);

async function validSignature(raw: string, header: string | null, secret: string): Promise<boolean> {
  if (!header?.startsWith("sha256=")) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw)));
  const hex = [...sig].map((b) => b.toString(16).padStart(2, "0")).join("");
  const given = header.slice(7);
  if (given.length !== hex.length) return false;
  let diff = 0;
  for (let i = 0; i < hex.length; i++) diff |= hex.charCodeAt(i) ^ given.charCodeAt(i);
  return diff === 0;
}

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);

  if (req.method === "GET") {
    const verify = Deno.env.get("WHATSAPP_VERIFY_TOKEN");
    if (verify && url.searchParams.get("hub.mode") === "subscribe" && url.searchParams.get("hub.verify_token") === verify) {
      return new Response(url.searchParams.get("hub.challenge") || "", { status: 200 });
    }
    return new Response("Forbidden", { status: 403 });
  }
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  const appSecret = Deno.env.get("WHATSAPP_APP_SECRET");
  const raw = await req.text();
  if (!appSecret) { console.error("WHATSAPP_APP_SECRET is not set"); return new Response("Not configured", { status: 503 }); }
  if (!(await validSignature(raw, req.headers.get("x-hub-signature-256"), appSecret))) return new Response("Bad signature", { status: 401 });

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const token = Deno.env.get("WHATSAPP_ACCESS_TOKEN") || "";
  let body: any;
  try { body = JSON.parse(raw); } catch { return new Response("Bad JSON", { status: 400 }); }

  const send = async (to: string, payload: Record<string, unknown>, key: string, leadId: string | null) => {
    try {
      const r = await fetch(`${GRAPH}/${PHONE_NUMBER_ID}/messages`, {
        method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ messaging_product: "whatsapp", recipient_type: "individual", to, ...payload }),
      });
      const j = await r.json().catch(() => ({}));
      await db.from("whatsapp_messages").insert({
        lead_id: leadId, recipient_phone: to, recipient_kind: "client", message_key: key, params: payload,
        status: r.ok ? "sent" : "failed", wamid: j?.messages?.[0]?.id ?? null, sent_at: r.ok ? new Date().toISOString() : null,
        failed_at: r.ok ? null : new Date().toISOString(), error_code: r.ok ? "" : String(j?.error?.code ?? r.status),
        error_detail: r.ok ? "" : String(j?.error?.message ?? "").slice(0, 500), attempts: 1,
      });
    } catch (e) { console.error("reply failed", e); }
  };

  for (const entry of body?.entry ?? []) {
    for (const change of entry?.changes ?? []) {
      if (change?.field !== "messages") continue;
      const v = change.value ?? {};
      // The Meta app may serve other WhatsApp numbers too: only handle Legal Wegal's number.
      if (String(v.metadata?.phone_number_id ?? "") !== PHONE_NUMBER_ID) continue;

      // ---- Delivery statuses for messages we sent ----
      for (const s of v.statuses ?? []) {
        const rank: Record<string, number> = { queued: 0, sending: 1, sent: 2, delivered: 3, read: 4, failed: 5 };
        const { data: m } = await db.from("whatsapp_messages").select("id,status").eq("wamid", s.id).maybeSingle();
        if (!m) continue;
        const ts = s.timestamp ? new Date(Number(s.timestamp) * 1000).toISOString() : new Date().toISOString();
        const up: Record<string, unknown> = {};
        if (s.status === "failed") Object.assign(up, { status: "failed", failed_at: ts, error_code: String(s.errors?.[0]?.code ?? ""), error_detail: String(s.errors?.[0]?.title ?? s.errors?.[0]?.message ?? "").slice(0, 500) });
        else if ((rank[s.status] ?? -1) > (rank[m.status] ?? -1)) up.status = s.status;
        if (s.status === "sent") up.sent_at = ts;
        if (s.status === "delivered") up.delivered_at = ts;
        if (s.status === "read") up.read_at = ts;
        if (Object.keys(up).length) await db.from("whatsapp_messages").update(up).eq("id", m.id);
      }

      // ---- Client messages and button taps ----
      for (const msg of v.messages ?? []) {
        const from = String(msg.from || "");
        const ctx = msg.context?.id ?? null;
        const buttonText = msg.button?.text ?? msg.interactive?.button_reply?.title ?? msg.interactive?.list_reply?.title ?? null;
        const payloadId = msg.button?.payload ?? msg.interactive?.button_reply?.id ?? msg.interactive?.list_reply?.id ?? null;
        const text = msg.text?.body ?? null;


        // Find the lead: first by the message they replied to, then by phone number.
        let leadId: string | null = null;
        if (ctx) {
          const { data: om } = await db.from("whatsapp_messages").select("lead_id").eq("wamid", ctx).maybeSingle();
          leadId = om?.lead_id ?? null;
        }
        if (!leadId) {
          const ten = last10(from);
          if (ten.length === 10) {
            const { data: cands } = await db.from("leads").select("id,phone,updated_at").ilike("phone", `%${ten.slice(-4)}%`).order("updated_at", { ascending: false }).limit(50);
            leadId = (cands ?? []).find((c: any) => last10(c.phone) === ten)?.id ?? null;
          }
        }
        const { data: inb } = await db.from("whatsapp_inbound").insert({
          wamid: msg.id, from_phone: from, lead_id: leadId, message_type: String(msg.type ?? ""), body: String(text ?? buttonText ?? ""),
          button_payload: String(payloadId ?? ""), context_wamid: String(ctx ?? ""), raw: msg,
        }).select("id").single();
        if (!inb) continue; // already received (Meta retries the same message) or could not be stored

        const word = String(buttonText ?? text ?? "").trim().toLowerCase();
        const nowIso = new Date().toISOString();
        let action = "recorded";
        const lead = leadId ? (await db.from("leads").select("id,stage,notes").eq("id", leadId).maybeSingle()).data : null;
        const setLead = async (patch: Record<string, unknown>) => { if (lead) await db.from("leads").update({ ...patch, updated_at: nowIso }).eq("id", lead.id); };
        // Returns the offline reply text when the call has to wait for working hours, else null.
        const callback = async (at: Date, note: string): Promise<string | null> => {
          let when = at, off: string | null = null;
          if (offHours(at)) { const n = nextOpen(at < new Date() ? new Date() : at); when = n.at; off = TXT.offline(n.day); }
          await setLead({ callback_due_at: when.toISOString(), callback_note: note + (off ? " (asked outside working hours)" : "") });
          return off;
        };

        if (["stop", "unsubscribe", "stop all"].includes(word)) {
          await setLead({ whatsapp_opt_in: false, whatsapp_opted_out_at: nowIso, whatsapp_optout_reason: "Client replied STOP" });
          await send(from, { type: "text", text: { body: TXT.stop } }, "ack_stop", leadId); action = "opted_out";
        } else if (word === "start") {
          await setLead({ whatsapp_opt_in: true, whatsapp_opted_out_at: null, whatsapp_optout_reason: "" });
          await send(from, { type: "text", text: { body: TXT.start } }, "ack_start", leadId); action = "opted_in";
        } else if (payloadId && SLOTS.some((s) => s.id === payloadId)) {
          const s = SLOTS.find((x) => x.id === payloadId)!;
          const off = await callback(s.at(), `Client chose on WhatsApp: ${s.title}`);
          await send(from, { type: "text", text: { body: off ?? TXT.slotDone(s.when) } }, "ack_slot", leadId); action = "callback_" + s.id;
        } else if (word === "call later") {
          await send(from, { type: "interactive", interactive: { type: "list", body: { text: TXT.slotIntro }, action: { button: "Choose a time", sections: [{ title: "Call me", rows: SLOTS.map((s) => ({ id: s.id, title: s.title })) }] } } }, "slot_list", leadId);
          action = "slot_list_sent";
        } else if (word === "call me in 1 hour") {
          const off = await callback(SLOTS[0].at(), "Client asked on WhatsApp: call in 1 hour");
          await send(from, { type: "text", text: { body: off ?? TXT.slotDone(SLOTS[0].when) } }, "ack_slot", leadId); action = "callback_1h";
        } else if (word === "tomorrow") {
          await callback(ist(1, 11), "Client asked on WhatsApp: call tomorrow");
          await send(from, { type: "text", text: { body: TXT.slotDone("tomorrow") } }, "ack_slot", leadId); action = "callback_tomorrow";
        } else if (["call me now", "call me back", "call me", "need help", "restart work"].includes(word)) {
          const off = await callback(new Date(), `Client tapped "${buttonText ?? text}" on WhatsApp`);
          await send(from, { type: "text", text: { body: off ?? TXT.callNow } }, "ack_call", leadId); action = off ? "callback_next_working_hours" : "callback_now";
        } else if (word === "not interested") {
          if (lead && EARLY_STAGES(String(lead.stage || ""))) await setLead({ stage: "Clear no lead", stage_date: nowIso.slice(0, 10), whatsapp_opt_in: false, whatsapp_opted_out_at: nowIso, whatsapp_optout_reason: "Not interested (WhatsApp button)" });
          else await setLead({ whatsapp_opt_in: false, whatsapp_opted_out_at: nowIso, whatsapp_optout_reason: "Not interested (WhatsApp button)" });
          await send(from, { type: "text", text: { body: TXT.notInterested } }, "ack_not_interested", leadId); action = "not_interested";
        } else if (word === "send details on whatsapp") {
          const off = await callback(new Date(), "Client asked for service details on WhatsApp");
          await send(from, { type: "text", text: { body: off ?? TXT.details } }, "ack_details", leadId); action = "details_requested";
        } else if (word === "paid already") {
          const off = await callback(new Date(), "Client says payment is already made - please verify");
          await send(from, { type: "text", text: { body: off ?? TXT.paidAlready } }, "ack_paid", leadId); action = "paid_claim";
        } else if (word === "pay later" || word === "not now") {
          action = word === "pay later" ? "pay_later" : "not_now";
        } else if (word === "happy") {
          await send(from, { type: "text", text: { body: TXT.happy } }, "ack_happy", leadId); action = "happy";
        } else if (text) {
          action = "free_text";
        }
        if (inb?.id) await db.from("whatsapp_inbound").update({ processed_at: new Date().toISOString(), action_taken: action }).eq("id", inb.id);
      }
    }
  }
  return json({ ok: true });
});
