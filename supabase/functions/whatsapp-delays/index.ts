// Delay summaries on WhatsApp (decided with Kunal, 13 Nov 2026):
//   11 AM and 4 PM IST: every RM / Work Executor with delays gets ONE summary
//                       ("25 calls and 3 work items are delayed … reported to Kunal sir").
//   4 PM:  items still delayed → one summary per staff member to each Admin.
//   11 AM: items delayed since before yesterday (still delayed after yesterday's 4 PM
//          escalation) → one summary per staff member to the Super Admin.
// It only QUEUES messages (public.whatsapp_messages); whatsapp-dispatch sends them.
// A call is "delayed" once its due date has passed (same rules as the CRM task list);
// a callback the client asked for is delayed once its time has passed; work is delayed
// once work_due_date has passed while the lead is in Group made / Work processed.
// Called by pg_cron with header x-dispatch-secret and body {"slot":"11am"|"4pm"}.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });
const istDay = (d = new Date()) => new Date(d.getTime() + 5.5 * 3600e3).toISOString().slice(0, 10);
const addDays = (day: string, n: number) => { const d = new Date(day + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };

type Lead = Record<string, any>;

// Next call date for a lead — a copy of tasksFor() in index.html (date part only).
function callDue(l: Lead, today: string): { day: string; kind: "call" | "work" | "assign"; at?: string } | null {
  const stage = String(l.stage || "");
  const active = !["False lead", "Clear no lead", "Work done"].includes(stage);
  if (l.callback_due_at && active) return { day: istDay(new Date(l.callback_due_at)), kind: "call", at: l.callback_due_at };
  if (stage === "Group made" || stage === "Work processed") {
    if (!l.executor_user_id) return { day: l.stage_date || today, kind: "assign" };
    return { day: l.work_due_date || addDays(l.stage_date || today, 7), kind: "work" };
  }
  if (stage === "Unverified" || stage.startsWith("Not picked")) {
    const n = stage === "Unverified" ? 0 : Number((stage.match(/(\d+)/) || [])[1] || 0);
    return { day: addDays(l.arrival || today, n < 3 ? 0 : 1), kind: "call" };
  }
  if (stage === "Verified") {
    const ix = l.followup_index || 0, sch = [0, 0, 1, 3, 5, 7, 11];
    return ix >= sch.length ? null : { day: addDays(l.verified_date || l.arrival || today, sch[ix]), kind: "call" };
  }
  if (stage === "Work dropped") {
    const ix = l.drop_index || 0, sch = [1, 3, 5];
    return ix >= sch.length ? null : { day: addDays(l.dropped_date || today, sch[ix]), kind: "call" };
  }
  if (stage === "Work done") {
    if (l.payment_status === "pending" && Number(l.pending_payment) > 0) return { day: l.payment_followup_date || today, kind: "call" };
    return { day: addDays(l.last_contact || l.completed_date || today, 7), kind: "call" };
  }
  return null;
}

Deno.serve(async (req: Request) => {
  const secret = Deno.env.get("WHATSAPP_DISPATCH_SECRET") || "";
  if (!(secret.length >= 24 && req.headers.get("x-dispatch-secret") === secret)) return json({ error: "Not allowed" }, 403);
  const body = await req.json().catch(() => ({}));
  const slot = body?.slot === "4pm" ? "4pm" : "11am";
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });

  const today = istDay(), yesterday = addDays(today, -1);
  const nowIso = new Date().toISOString();
  const { data: leads, error } = await db.from("leads").select(
    "id,stage,arrival,verified_date,followup_index,dropped_date,drop_index,last_contact,completed_date,payment_status,pending_payment,payment_followup_date,callback_due_at,executor_user_id,work_due_date,stage_date,owner_user_id,created_by");
  if (error) return json({ error: error.message }, 500);

  // Per staff member: delayed calls / work, and the part delayed since before yesterday.
  const per = new Map<string, { calls: number; work: number; oldCalls: number; oldWork: number }>();
  const bump = (uid: string | null, kind: "calls" | "work", old: boolean) => {
    if (!uid) return;
    const p = per.get(uid) ?? { calls: 0, work: 0, oldCalls: 0, oldWork: 0 };
    p[kind]++; if (old) p[kind === "calls" ? "oldCalls" : "oldWork"]++;
    per.set(uid, p);
  };
  for (const l of leads ?? []) {
    const due = callDue(l, today);
    if (!due) continue;
    const late = due.at ? due.at < nowIso : due.day < today;
    if (!late) continue;
    const old = due.day < yesterday;
    const rm = l.owner_user_id || l.created_by;
    if (due.kind === "work") bump(l.executor_user_id, "work", old);
    else if (due.kind === "assign") bump(rm, "work", old);
    else bump(rm, "calls", old);
  }

  const { data: roles } = await db.from("user_roles").select("user_id,role,whatsapp_number");
  const { data: users } = await db.auth.admin.listUsers({ page: 1, perPage: 1000 });
  const nameOf = (id: string) => {
    const u = users?.users?.find((x: any) => x.id === id);
    return u?.user_metadata?.full_name || (u?.email || "Team member").split("@")[0];
  };
  const phoneOf = (id: string) => roles?.find((r: any) => r.user_id === id)?.whatsapp_number || "";
  const admins = (roles ?? []).filter((r: any) => r.role === "admin" && r.whatsapp_number);
  const superAdmin = Deno.env.get("SUPER_ADMIN_WHATSAPP") || "918208221425";

  const rows: Record<string, unknown>[] = [];
  const label = slot === "4pm" ? "4 PM" : "11 AM";
  const when = `${label}, ${new Date(today + "T00:00:00Z").toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "UTC" })}`;
  for (const [uid, p] of per) {
    if (p.calls + p.work === 0) continue;
    const phone = phoneOf(uid);
    if (phone) rows.push({ recipient_phone: phone, recipient_kind: "staff", recipient_user_id: uid, message_key: "T-delay", template_name: "lw_t_delay_summary",
      params: [nameOf(uid), label, String(p.calls), String(p.work)], dedupe_key: `TD:${today}:${slot}:${uid}` });
    if (slot === "4pm") for (const a of admins) if (a.user_id !== uid)
      rows.push({ recipient_phone: a.whatsapp_number, recipient_kind: "admin", recipient_user_id: a.user_id, message_key: "T-escalate-admin", template_name: "lw_t_delay_escalation",
        params: [nameOf(uid), String(p.calls), String(p.work), when], dedupe_key: `TE:${today}:${uid}:${a.user_id}` });
    if (slot === "11am" && p.oldCalls + p.oldWork > 0)
      rows.push({ recipient_phone: superAdmin, recipient_kind: "super_admin", message_key: "T-escalate-sa", template_name: "lw_t_delay_escalation",
        params: [nameOf(uid), String(p.oldCalls), String(p.oldWork), when], dedupe_key: `TS:${today}:${uid}` });
  }
  const norm = (p: string) => { const d = String(p).replace(/\D/g, ""); return d.length === 10 ? "91" + d : d; };
  const clean = rows.map((r) => ({ ...r, recipient_phone: norm(String(r.recipient_phone)), scheduled_for: nowIso })).filter((r) => (r.recipient_phone as string).length >= 11);
  let queued = 0;
  if (clean.length) {
    const { data: ins, error: e2 } = await db.from("whatsapp_messages").upsert(clean, { onConflict: "dedupe_key", ignoreDuplicates: true }).select("id");
    if (e2) return json({ error: e2.message }, 500);
    queued = ins?.length ?? 0;
  }
  return json({ ok: true, slot, staff_with_delays: [...per.values()].filter((p) => p.calls + p.work > 0).length, queued });
});
