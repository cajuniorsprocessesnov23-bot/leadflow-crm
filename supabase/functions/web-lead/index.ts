// Web / ad enquiries -> LeadFlow CRM (Unverified lead).
// Three senders:
//   1. Our enquiry page (enquiry.html): JSON { name, phone, service, city, message, utm_source, utm_campaign, gclid, hp }
//   2. Google Ads lead form webhook: { google_key, user_column_data: [...], campaign_id, gcl_id, lead_id, is_test }
//      google_key must equal the GOOGLE_LEAD_KEY secret (set in Supabase -> Edge Functions -> Secrets).
//   3. Meta (Facebook / Instagram) lead ads webhook: object "page", field "leadgen". Signed with the
//      Meta app secret (WHATSAPP_APP_SECRET, same "Legal Wegal" app). Lead details are read with
//      META_PAGE_TOKEN (a Page token with leads_retrieval). GET answers Meta's webhook verification
//      with META_VERIFY_TOKEN (or WHATSAPP_VERIFY_TOKEN).
// Owner = Settings → person for the service; else Manage Users → "WhatsApp leads go to"; else first staff member.
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

type Form = { name: string; phone: string; city: string; email: string; text: string; source: string; campaign: string; click: string; service: string; test: boolean };
type Out = { status: number; body: Record<string, unknown> };
const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });

async function processLead(f: Form): Promise<Out> {
  const ten = last10(f.phone);
  const digits = String(f.phone).replace(/\D/g, "");
  const indian = ten.length === 10 && /^[6-9]/.test(ten) && (digits.length === 10 || (digits.length === 12 && digits.startsWith("91")) || (digits.length === 11 && digits.startsWith("0")));
  if (!f.name || !indian) return { status: 400, body: { error: "Please enter your name and a valid 10-digit Indian mobile number." } };
  if (f.test) return { status: 200, body: { ok: true, test: true } }; // Google "Send test data": accepted, nothing saved

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
    return { status: 200, body: { ok: true, existing: true } };
  }

  // Owner: Settings → person for the service; else Manage Users → "WhatsApp leads go to"; else first staff member.
  const { data: chosen } = await db.rpc("lead_owner_for_services", { p_services: types });
  const { data: roles } = await db.from("user_roles").select("user_id,role");
  const ownerId: string | undefined = (roles ?? []).find((r: any) => r.user_id === chosen)?.user_id
    ?? (roles ?? []).find((r: any) => r.role === "staff")?.user_id ?? (roles ?? [])[0]?.user_id;
  if (!ownerId) return { status: 500, body: { error: "CRM not ready" } };
  const { data: u } = await db.auth.admin.getUserById(ownerId);
  const ownerName = u?.user?.user_metadata?.full_name || (u?.user?.email || "Team").split("@")[0];

  const { data: code } = await db.rpc("next_lead_code");
  const { error } = await db.from("leads").insert({
    id: crypto.randomUUID(), created_by: ownerId, created_by_name: ownerName, owner_user_id: ownerId,
    name: f.name, phone: ten, stage: "Unverified", arrival: nowIst.toISOString().slice(0, 10), source: f.source,
    lead_code: code ?? null, lead_types: types, whatsapp_opt_in: true,
    notes: `${f.source} enquiry (${stamp}). ${detail}`.slice(0, 5000),
  });
  if (error) { console.error("web-lead insert failed", error.message); return { status: 500, body: { error: "Could not save. Please call or WhatsApp us." } }; }
  return { status: 200, body: { ok: true } };
}

async function validMetaSignature(raw: string, header: string | null): Promise<boolean> {
  const secret = Deno.env.get("WHATSAPP_APP_SECRET") || "";
  if (!secret || !header?.startsWith("sha256=")) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw)));
  const hex = [...sig].map((b) => b.toString(16).padStart(2, "0")).join("");
  const want = header.slice(7);
  if (hex.length !== want.length) return false;
  let diff = 0; for (let i = 0; i < hex.length; i++) diff |= hex.charCodeAt(i) ^ want.charCodeAt(i);
  return diff === 0;
}

async function metaLeadToForm(leadgenId: string): Promise<Form | null> {
  const token = Deno.env.get("META_PAGE_TOKEN");
  if (!token) { console.error("META_PAGE_TOKEN is not set"); return null; }
  const r = await fetch(`https://graph.facebook.com/v24.0/${encodeURIComponent(leadgenId)}?fields=field_data,campaign_name,adset_name,ad_name,form_id,is_organic`, { headers: { Authorization: `Bearer ${token}` } });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { console.error("Meta lead fetch failed", j?.error?.message); return null; }
  const fd: { name: string; values: string[] }[] = j.field_data ?? [];
  const get = (...keys: string[]) => clean(fd.find((x) => keys.includes(String(x.name).toLowerCase()))?.values?.[0]);
  const known = ["full_name", "first_name", "last_name", "phone_number", "phone", "email", "city"];
  const extra = fd.filter((x) => !known.includes(String(x.name).toLowerCase())).map((x) => `${clean(x.name, 60).replace(/_/g, " ")}: ${clean((x.values || []).join(", "))}`).join("; ");
  return {
    name: get("full_name") || [get("first_name"), get("last_name")].filter(Boolean).join(" "),
    phone: get("phone_number", "phone"), city: get("city"), email: get("email"), text: extra,
    source: "Meta Ads", campaign: clean([j.campaign_name, j.adset_name, j.ad_name].filter(Boolean).join(" / "), 160), click: clean(leadgenId, 60), service: "", test: false,
  };
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("origin");
  const H = cors(origin);
  const out = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: H });
  if (req.method === "OPTIONS") return new Response("ok", { headers: H });

  // Meta webhook verification (GET with hub.* parameters).
  if (req.method === "GET") {
    const u = new URL(req.url);
    const want = Deno.env.get("META_VERIFY_TOKEN") || Deno.env.get("WHATSAPP_VERIFY_TOKEN") || "";
    if (u.searchParams.get("hub.mode") === "subscribe" && want && u.searchParams.get("hub.verify_token") === want)
      return new Response(u.searchParams.get("hub.challenge") ?? "", { status: 200 });
    return out({ error: "Not allowed" }, 403);
  }
  if (req.method !== "POST") return out({ error: "POST only" }, 405);

  const raw = await req.text();
  let body: any;
  try { body = JSON.parse(raw); } catch { return out({ error: "Bad request" }, 400); }

  // ---- Meta lead ads ----
  if (body?.object === "page") {
    if (!(await validMetaSignature(raw, req.headers.get("x-hub-signature-256")))) return out({ error: "Bad signature" }, 403);
    const results: unknown[] = [];
    for (const e of body.entry ?? []) for (const c of e.changes ?? []) {
      if (c.field !== "leadgen" || !c.value?.leadgen_id) continue;
      const f = await metaLeadToForm(String(c.value.leadgen_id));
      if (!f) { results.push({ leadgen_id: c.value.leadgen_id, error: "could not read lead" }); continue; }
      const r = await processLead(f);
      results.push({ leadgen_id: c.value.leadgen_id, ...r.body });
    }
    return out({ ok: true, results }); // always 200 so Meta does not retry forever
  }

  // ---- Google Ads lead form ----
  if (body && "google_key" in body) {
    const key = Deno.env.get("GOOGLE_LEAD_KEY");
    if (!key || body.google_key !== key) return out({ error: "Forbidden" }, 403);
    const col = (id: string) => clean((body.user_column_data ?? []).find((c: any) => c.column_id === id)?.string_value);
    const extra = (body.user_column_data ?? []).filter((c: any) => !["FULL_NAME", "FIRST_NAME", "LAST_NAME", "PHONE_NUMBER", "EMAIL", "CITY"].includes(c.column_id))
      .map((c: any) => `${clean(c.column_name || c.column_id, 60)}: ${clean(c.string_value)}`).join("; ");
    const r = await processLead({
      name: col("FULL_NAME") || [col("FIRST_NAME"), col("LAST_NAME")].filter(Boolean).join(" "),
      phone: col("PHONE_NUMBER"), city: col("CITY"), email: col("EMAIL"), text: extra,
      source: "Google Ads", campaign: clean(body.campaign_id, 40), click: clean(body.gcl_id, 200), service: "", test: !!body.is_test,
    });
    return out(r.body, r.status);
  }

  // ---- Our enquiry page ----
  if (clean(body?.hp)) return out({ ok: true }); // honeypot filled = bot; pretend success
  const r = await processLead({
    name: clean(body?.name, 120), phone: clean(body?.phone, 20), city: clean(body?.city, 80), email: "", text: clean(body?.message, 500),
    source: /google|gads|adwords/i.test(clean(body?.utm_source)) || clean(body?.gclid) ? "Google Ads"
      : /facebook|meta|instagram|fb|ig/i.test(clean(body?.utm_source)) ? "Meta Ads" : "Website",
    campaign: clean(body?.utm_campaign, 80), click: clean(body?.gclid, 200), service: clean(body?.service, 60), test: false,
  });
  return out(r.body, r.status);
});
