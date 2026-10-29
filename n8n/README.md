# LeadFlow CRM + n8n automation

This folder contains an importable n8n webhook workflow. The CRM now emits server-side events for new leads, payment collections, and pending-payment updates. It does not send messages until n8n is configured and the deployment succeeds.

## 1. Import the workflow
1. Create or log in to an n8n instance.
2. Import `n8n/leadflow-event-messages.json`.
3. Open the **Send WhatsApp via Twilio** node and create/select an HTTP Basic Auth credential named **Twilio API Basic Auth**. Username = Twilio Account SID; password = Twilio Auth Token.
4. Create n8n Variables (Settings → Variables) named:
   - `LEADFLOW_WEBHOOK_SECRET`: a long random secret you generate.
   - `TWILIO_ACCOUNT_SID`: your Account SID.
   - `TWILIO_WHATSAPP_FROM`: your registered WhatsApp sender, e.g. `+14155238886` (no `whatsapp:` prefix needed).
5. Activate the workflow. Copy its Production webhook URL, which should end in `/webhook/leadflow-events`.

## 2. Configure Supabase secrets
In Supabase Dashboard → Edge Functions → Secrets, add:
- `N8N_WEBHOOK_URL` = the n8n Production webhook URL.
- `N8N_WEBHOOK_SECRET` = exactly the same random secret as `LEADFLOW_WEBHOOK_SECRET`.

The CRM calls the deployed `n8n-dispatch` Supabase Edge Function with the signed-in user's JWT. The function verifies the user and sends the event to n8n with `x-leadflow-secret`. Credentials are never placed in the browser or committed to GitHub.

## 3. Current event types
- `lead.created`: sends a welcome message after a lead is added, only when the lead's **WhatsApp consent** checkbox is checked.
- `payment.confirmed`: sends a receipt-style confirmation after a collection is recorded, only when consent is checked.
- `payment.reminder_due`: emitted when a pending balance is recorded/updated, only when consent is checked. The current webhook template sends it immediately; change this to a queue if you want reminders at a scheduled time.

## 4. Scheduled follow-ups and payment reminders
This workflow handles event-driven messages. Scheduled follow-ups require a second n8n Schedule Trigger workflow that reads the CRM's due-task rules from Supabase, deduplicates sends, and records the last notification timestamp. Do not activate bulk scheduled sending until a delivery log/idempotency table and customer WhatsApp opt-in checks are in place. LeadFlow's existing due-call schedule is calculated in the frontend and is not yet exposed as a server-side due-task API.

## Important setup and compliance
- This is a workflow template, not an already-connected n8n instance.
- You must provide an n8n instance URL, activate the workflow, configure secrets/credentials, and complete Twilio/WhatsApp business registration.
- Only message people who opted in. WhatsApp business-initiated messages outside the 24-hour service window generally require an approved template. The sample messages here are free-form and are suitable only when the WhatsApp policy permits them.
- Test with your own opted-in number before enabling real clients.
