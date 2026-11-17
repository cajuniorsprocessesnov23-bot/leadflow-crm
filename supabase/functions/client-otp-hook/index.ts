// Supabase Auth "Send SMS" hook: delivers the client-portal login code on WhatsApp instead of SMS.
// Supabase calls this when a client asks for a code (signInWithOtp({ phone })).
// Secrets: SEND_SMS_HOOK_SECRET (from Auth → Hooks, "v1,whsec_..."), WHATSAPP_ACCESS_TOKEN,
// WHATSAPP_PHONE_NUMBER_ID. Template: CLIENT_OTP_TEMPLATE (default "lw_login_otp", category
// AUTHENTICATION with a copy-code button).
// JWT verification must be OFF for this function (Supabase signs the call with the hook secret).

const GRAPH = "https://graph.facebook.com/v24.0";

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

async function verify(req: Request, body: string): Promise<boolean> {
  const raw = Deno.env.get("SEND_SMS_HOOK_SECRET") || "";
  const secret = raw.replace(/^v1,/, "").replace(/^whsec_/, "");
  const id = req.headers.get("webhook-id"), ts = req.headers.get("webhook-timestamp"), sigs = req.headers.get("webhook-signature");
  if (!secret || !id || !ts || !sigs) return false;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 300) return false;
  const key = await crypto.subtle.importKey("raw", b64ToBytes(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${id}.${ts}.${body}`)));
  const expected = btoa(String.fromCharCode(...mac));
  return sigs.split(" ").some((s) => s.split(",")[1] === expected);
}

Deno.serve(async (req) => {
  const body = await req.text();
  if (!(await verify(req, body))) {
    return new Response(JSON.stringify({ error: { http_code: 401, message: "Invalid signature" } }), { status: 401, headers: { "content-type": "application/json" } });
  }
  let payload: any;
  try { payload = JSON.parse(body); } catch { return new Response("{}", { status: 400 }); }
  const phone = String(payload?.user?.phone || "").replace(/\D/g, "");
  const otp = String(payload?.sms?.otp || "");
  if (!phone || !otp) {
    return new Response(JSON.stringify({ error: { http_code: 400, message: "Missing phone or code" } }), { status: 400, headers: { "content-type": "application/json" } });
  }
  const to = phone.length === 10 ? "91" + phone : phone;
  const template = Deno.env.get("CLIENT_OTP_TEMPLATE") || "lw_login_otp";
  const res = await fetch(`${GRAPH}/${Deno.env.get("WHATSAPP_PHONE_NUMBER_ID")}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${Deno.env.get("WHATSAPP_ACCESS_TOKEN")}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      messaging_product: "whatsapp", to, type: "template",
      template: {
        name: template, language: { code: "en" },
        components: [
          { type: "body", parameters: [{ type: "text", text: otp }] },
          { type: "button", sub_type: "url", index: "0", parameters: [{ type: "text", text: otp }] },
        ],
      },
    }),
  });
  if (!res.ok) {
    console.error("OTP WhatsApp send failed", res.status, (await res.text()).slice(0, 400));
    return new Response(JSON.stringify({ error: { http_code: 500, message: "Could not send the code on WhatsApp. Please try again." } }), { status: 500, headers: { "content-type": "application/json" } });
  }
  return new Response("{}", { headers: { "content-type": "application/json" } });
});
