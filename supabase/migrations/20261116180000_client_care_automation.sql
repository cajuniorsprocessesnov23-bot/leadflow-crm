-- Client care automation (16 Nov 2026)
-- What this adds (all additive):
--   1. client_renewals: renewal / due dates per client (e.g. FSSAI renewal, trademark renewal,
--      GST annual return). Anyone who can see the lead can add, edit or close them.
--   2. Renewal reminders: daily at 9:05 AM IST, the client gets a WhatsApp 15 days and 3 days
--      before each open due date (template lw_c_renewal).
--   3. Review requests: daily at 9:05 AM IST, clients whose work was completed 2-7 days ago,
--      review not yet taken and not asked before, get the review request with your Google
--      review link (template lw_c13_review_request). Nothing is sent until the link is saved.
--   4. Birthday wishes: daily at 9:05 AM IST, clients whose birthday is today get the approved
--      birthday template (lw_c15_birthday), once a year.
--   5. Evening summary: Mon-Sat 7:50 PM IST, the whatsapp-delays function sends Kunal the
--      day's summary (template lw_t_daily_summary). It runs before 8 PM because WhatsApp
--      messages are only sent 9 AM - 8 PM.
-- Impact on existing data: none (one new empty table).

create table if not exists public.client_renewals (
  id uuid primary key default gen_random_uuid(),
  lead_id text not null references public.leads(id) on delete cascade,
  service text not null,
  due_date date not null,
  note text not null default '',
  status text not null default 'open' check (status in ('open', 'done', 'cancelled')),
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists client_renewals_due_idx on public.client_renewals (due_date) where status = 'open';
create index if not exists client_renewals_lead_idx on public.client_renewals (lead_id);
alter table public.client_renewals enable row level security;
drop policy if exists client_renewals_all on public.client_renewals;
create policy client_renewals_all on public.client_renewals for all to authenticated
  using (private.can_access_lead(lead_id)) with check (private.can_access_lead(lead_id));

create or replace function private.wa_client_care() returns jsonb
language plpgsql security definer set search_path = '' as $$
declare v_today date := (now() at time zone 'Asia/Kolkata')::date; v_link text := (select value from private.app_settings where key = 'google_review_link');
  r record; v_ren int := 0; v_rev int := 0; v_bd int := 0;
begin
  -- Renewals: 15 and 3 days before.
  for r in select c.*, l.name, l.phone, l.whatsapp_opt_in from public.client_renewals c join public.leads l on l.id = c.lead_id
           where c.status = 'open' and c.due_date - v_today in (15, 3) and l.whatsapp_opt_in loop
    perform private.wa_enqueue(r.lead_id, r.phone, 'client', null, 'C-renew', 'lw_c_renewal',
      jsonb_build_array(r.name, r.service, to_char(r.due_date, 'DD Mon YYYY')), 'RN:' || r.id || ':' || (r.due_date - v_today));
    v_ren := v_ren + 1;
  end loop;
  -- Review requests.
  if coalesce(v_link, '') <> '' then
    for r in select l.* from public.leads l
             where l.stage = 'Work done' and not coalesce(l.review_taken, false) and l.whatsapp_opt_in
               and l.completed_date between v_today - 7 and v_today - 2
               and not exists (select 1 from public.whatsapp_messages m where m.lead_id = l.id and m.message_key in ('C13', 'C-review')) loop
      perform private.wa_enqueue(r.id, r.phone, 'client', null, 'C-review', 'lw_c13_review_request',
        jsonb_build_array(r.name, v_link), 'RV:' || r.id);
      v_rev := v_rev + 1;
    end loop;
  end if;
  -- Birthdays.
  for r in select l.* from public.leads l
           where l.birthday is not null and to_char(l.birthday, 'MM-DD') = to_char(v_today, 'MM-DD')
             and l.whatsapp_opt_in and l.stage not in ('False lead', 'Clear no lead') loop
    perform private.wa_enqueue(r.id, r.phone, 'client', null, 'C15', 'lw_c15_birthday',
      jsonb_build_array(r.name), 'BD:' || r.id || ':' || extract(year from v_today));
    v_bd := v_bd + 1;
  end loop;
  return jsonb_build_object('renewals', v_ren, 'reviews', v_rev, 'birthdays', v_bd);
end $$;

select cron.unschedule(jobname) from cron.job where jobname in ('client-care-daily', 'whatsapp-evening-summary');
select cron.schedule('client-care-daily', '35 3 * * *', $$select private.wa_client_care()$$);  -- 9:05 AM IST
select cron.schedule('whatsapp-evening-summary', '20 14 * * 1-6', $job$
  select net.http_post(url := 'https://smedmzwiddhmxaznqoen.supabase.co/functions/v1/whatsapp-delays',
    headers := jsonb_build_object('Content-Type', 'application/json',
      'x-dispatch-secret', (select decrypted_secret from vault.decrypted_secrets where name = 'wa_dispatch_secret')),
    body := '{"slot":"summary"}'::jsonb, timeout_milliseconds := 60000)
$job$);
