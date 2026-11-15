-- Applied 15 Nov 2026 via the SQL editor. Runs the whatsapp-dispatch Edge Function every
-- 5 minutes (it sends nothing outside 9 AM-8 PM IST). The header secret lives in Vault as
-- 'wa_dispatch_secret' and must equal the Edge Function secret WHATSAPP_DISPATCH_SECRET.
create extension if not exists pg_cron;
create extension if not exists pg_net;
-- select vault.create_secret('<same value as WHATSAPP_DISPATCH_SECRET>', 'wa_dispatch_secret');
select cron.schedule('whatsapp-dispatch-every-5-min', '*/5 * * * *', $job$
  select net.http_post(
    url := 'https://smedmzwiddhmxaznqoen.supabase.co/functions/v1/whatsapp-dispatch',
    headers := jsonb_build_object('Content-Type', 'application/json',
      'x-dispatch-secret', (select decrypted_secret from vault.decrypted_secrets where name = 'wa_dispatch_secret')),
    body := '{}'::jsonb, timeout_milliseconds := 30000)
$job$);
