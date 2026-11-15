// Web / ad enquiries -> LeadFlow CRM (Unverified lead).
// Two senders:
//   1. Our enquiry page (enquiry.html): JSON { name, phone, service, city, message, utm_source, utm_campaign, gclid, hp }
//   2. Google Ads lead form webhook: { google_key, user_column_data: [...], campaign_id, gcl_id, lead_id, is_test }
//      google_key must equal the GOOGLE_LEAD_KEY secret (set in Supabase -> Edge Functions -> Secrets).
// Owner = the person chosen in Manage Users -> "WhatsApp leads go to" (same setting), else first staff member.
// An existing lead with the same mobile is not duplicated: a note is added to it instead.
// Deploy with "Enforce JWT verification" OFF (the public page and Google cannot send a Supabase JWT).
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ORIGINS = ["https://leadflow-crm.cajuniorsprocessesnov23.workers.dev", "https://legalwegal.com", "https://www.legalwegal.com"];
const cors = (origin: string | null) => ({
  "Access-Control-Allow-Origin": origin && ORIGINS.includes(origin) ? origin : ORIGINS[0],
  "Access-Control-Allow-Headers": "content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
});

// Page slug or free text -> CRM lead type (must exist in lead_type_options).
const SERVICE_WORDS: Record<string, RegExp> = {
  "GST": /\bgst(in|r\d*)?\b|goods and services tax/i,
  "Trademark": /trade ?mark|\btm\b|brand (name )?regist|logo regist/i,
  "FSSAI": /fssai|food (licen[cs]e|regist)/i,
  "IEC": /\biec\b|import ?export|import-export code/i,
  "HUID / Hallmarking": /huid|hallmark|\bbis\b.*(gold|jewel)|jewel(le)?ry regist/i,
  "Company Registration": /company (regist|incorporat|formation)|pvt\.? ?ltd|private limited|\bopc\b|one person company|incorporat/i,
  "LLP Registration": /\bllp\b|limited liability partnership/i,
  "MSME / Udyam": /msme|udyam|udyog/i,
  "Income Tax": /income ?tax|\bitr\b|tax return|\btds\b/i,
  "Accounting": /accounting|book ?keeping|\baccounts\b|\btally\b/i,
};
const SLUGS: Record<string, string> = { gst: "GST", trademark: "Trademark", fssai: "FSSAI", iec: "IEC", huid: "HUID / Hallmarking" };

const clean = (v: unknown, n = 200) => String(v ?? "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, n);
const last10 = (p: string) => String(p || "").replace(/\D/g, "").slice(-10);

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("origin");
  const H = cors(origin);
  const out = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: H });
  if (req.method === "OPTIONS") return new Response("ok", { headers: H });
  if (req.method !== "POST") return out({ error: "POST only" }, 405);

  let body: any;
  try { body = await req.json(); } catch { return out({ error: "Bad request" }, 400); }

  // ---- Normalise both senders into one shape ----
  let f: { name: string; phone: string; city: string; email: string; text: string; source: string; campaign: string; click: string; service: string; test: boolean };
  if (body && "google_key" in body) {
    const key = Deno.env.get("GOOGLE_LEAD_KEY");
    if (!key || body.google_key !== key) return out({ error: "Forbidden" }, 403);
    const col = (id: string) => clean((body.user_column_data ?? []).find((c: any) => c.column_id === id)?.string_value);
    const extra = (body.user_column_data ?? []).filter((c: any) => !["FULL_NAME", "FIRST_NAME", "LAST_NAME", "PHONE_NUMBER", "EMAIL", "CITY"].includes(c.column_id))
      .map((c: any) => `${clean(c.column_name || c.column_id, 60)}: ${clean(c.string_value)}`).join("; ");
    f = {
      name: col("FULL_NAME") || [col("FIRST_NAME"), col("LAST_NAME")].filter(Boolean).join(" "),
      phone: col("PHONE_NUMBER"), city: col("CITY"), email: col("EMAIL"), text: extra,
      source: "Google Ads", campaign: clean(body.campaign_id, 40), click: clean(body.gcl_id, 200), service: "", test: !!body.is_test,
    };
  } else {
    if (clean(body?.hp)) return out({ ok: true }); // honeypot filled = bot; pretend success
    f = {
      name: clean(body?.name, 120), phone: clean(body?.phone, 20), city: clean(body?.city, 80), email: "", text: clean(body?.message, 500),
      source: /google|gads|adwords/i.test(clean(body?.utm_source)) || clean(body?.gclid) ? "Google Ads"
        : /facebook|meta|instagram|fb|ig/i.test(clean(body?.utm_source)) ? "Meta Ads" : "Website",
      campaign: clean(body?.utm_campaign, 80), click: clean(body?.gclid, 200), service: clean(body?.service, 60), test: false,
    };
  }

  const ten = last10(f.phone);
  const digits = String(f.phone).replace(/\D/g, "");
  const indian = ten.length === 10 && /^[6-9]/.test(ten) && (digits.length === 10 || (digits.length === 12 && digits.startsWith("91")) || (digits.length === 11 && digits.startsWith("0")));
  if (!f.name || !indian) return out({ error: "Please enter your name and a valid 10-digit Indian mobile number." }, 400);
  if (f.test) return out({ ok: true, test: true }); // Google "Send test data": accepted, nothing saved

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });

  // Service: explicit page choice first, then words in campaign name / message.
  const { data: lt } = await db.from("lead_type_options").select("name,active");
  const active = (lt ?? []).filter((t: any) => t.active).map((t: any) => t.name as string);
  const picked = SLUGS[f.service.toLowerCase()] || (active.includes(f.service) ? f.service : "");
  const hay = `${f.service} ${f.campaign} ${f.text}`;
  const types = [...new Set([picked, ...Object.entries(SERVICE_WORDS).filter(([, re]) => re.test(hay)).map(([n]) => n)])].filter((n) => n && active.includes(n));

  const nowIst = new Date(Date.now() + 5.5 * 3600e3);
  const stamp = nowIst.toISOString().slice(0, 16).replace("T", " ");
  const detail = [types.length ? `Service: ${types.join(", ")}` : "", f.city && `City: ${f.city}`, f.email && `Email: ${f.email}`, f.text && `Message: ${f.text}`,
    f.campaign && `Campaign: ${f.campaign}`, f.click && `Click ID: ${f.click}`].filter(Boolean).join(" · ");

  // Already in the CRM? Add a note, don't duplicate.
  const { data: cands } = await db.from("leads").select("id,phone,notes,lead_types").ilike("phone", `%${ten.slice(-4)}%`).limit(50);
  const existing = (cands ?? []).find((c: any) => last10(c.phone) === ten);
  if (existing) {
    const merged = [...new Set([...(existing.lead_types ?? []), ...types])];
    await db.from("leads").update({
      notes: `${existing.notes ? existing.notes + "\n" : ""}[${stamp}] Enquired again via ${f.source}. ${detail}`.slice(0, 5000),
      lead_types: merged, updated_at: new Date().toISOString(),
    }).eq("id", existing.id);
    return out({ ok: true, existing: true });
  }

  // Owner: the person the Super Admin chose; else first staff member; else anyone with a role.
  const { data: chosen } = await db.rpc("get_whatsapp_lead_owner");
  const { data: roles } = await db.from("user_roles").select("user_id,role");
  const ownerId: string | undefined = (roles ?? []).find((r: any) => r.user_id === chosen)?.user_id
    ?? (roles ?? []).find((r: any) => r.role === "staff")?.user_id ?? (roles ?? [])[0]?.user_id;
  if (!ownerId) return out({ error: "CRM not ready" }, 500);
  const { data: u } = await db.auth.admin.getUserById(ownerId);
  const ownerName = u?.user?.user_metadata?.full_name || (u?.user?.email || "Team").split("@")[0];

  const { data: code } = await db.rpc("next_lead_code");
  const { error } = await db.from("leads").insert({
    id: crypto.randomUUID(), created_by: ownerId, created_by_name: ownerName, owner_user_id: ownerId,
    name: f.name, phone: ten, stage: "Unverified", arrival: nowIst.toISOString().slice(0, 10), source: f.source,
    lead_code: code ?? null, lead_types: types, whatsapp_opt_in: true,
    notes: `${f.source} enquiry (${stamp}). ${detail}`.slice(0, 5000),
  });
  if (error) { console.error("web-lead insert failed", error.message); return out({ error: "Could not save. Please call or WhatsApp us." }, 500); }
  return out({ ok: true });
});
