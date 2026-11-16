-- Team features (16 Nov 2026)
-- What this adds (all additive; no existing rows are deleted):
--   1. Live updates: leads and whatsapp_inbound are added to Supabase Realtime, so the CRM
--      refreshes and shows alerts without reloading. Row security still applies.
--   2. find_lead_by_phone(phone): tells a user if a mobile number already exists (lead ID,
--      name, owner) even when the lead belongs to someone else. Returns no other data.
--   3. leads.work_checklist (jsonb, default {}): ticks for the Work Executor's checklist.
--   4. lead_type_options.documents (text): documents needed per service. Filled with
--      standard lists for existing services; Admins can edit them.
--   5. Settings: upi_id and service_owner_map in private.app_settings, read by Admins and
--      changed only by the Super Admin through get_app_settings() / set_app_setting().
--   6. lead_owner_for_services(services): picks the owner for auto-created leads
--      (service map first, then "WhatsApp leads go to", else nothing).
--   7. Document checklist on WhatsApp: when a lead becomes Verified, the client gets the
--      document list for their services (template lw_c_documents, sent 9 AM - 8 PM).
--   8. Payment reminders: daily at 11:15 AM (Mon-Sat), clients with pending payment get a
--      polite reminder with the UPI ID every 3 days, at most 5 times
--      (template lw_c_payment_reminder). Nothing is sent until a UPI ID is saved.
-- Impact on existing data: one new column on leads (empty), one on lead_type_options
-- (filled with default document lists), two new settings rows.

-- 1. Realtime ------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'leads') then
    alter publication supabase_realtime add table public.leads;
  end if;
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'whatsapp_inbound') then
    alter publication supabase_realtime add table public.whatsapp_inbound;
  end if;
end $$;

-- 2. Duplicate check ----------------------------------------------------------------
create or replace function public.find_lead_by_phone(p_phone text)
returns table (lead_id text, lead_code text, name text, owner_name text, stage text, can_open boolean)
language sql stable security definer set search_path to '' as $$
  select l.id, l.lead_code, l.name,
         private.wa_staff_name(coalesce(l.owner_user_id, l.created_by)),
         l.stage, private.can_access_lead(l.id)
  from public.leads l
  where length(regexp_replace(coalesce(p_phone, ''), '\D', '', 'g')) >= 10
    and right(regexp_replace(coalesce(l.phone, ''), '\D', '', 'g'), 10) = right(regexp_replace(p_phone, '\D', '', 'g'), 10)
  order by l.created_at
  limit 3
$$;
revoke all on function public.find_lead_by_phone(text) from public, anon;
grant execute on function public.find_lead_by_phone(text) to authenticated;

-- 3. Executor checklist ---------------------------------------------------------------
alter table public.leads add column if not exists work_checklist jsonb not null default '{}'::jsonb;

-- 4. Documents per service ------------------------------------------------------------
alter table public.lead_type_options add column if not exists documents text not null default '';
update public.lead_type_options o set documents = d.docs
from (values
  ('GST', 'PAN card, Aadhaar card, passport-size photo, business address proof (electricity bill or rent agreement with owner NOC), cancelled cheque or bank statement'),
  ('Trademark', 'Brand name and logo (if any), PAN and Aadhaar of the applicant, business address proof, date you started using the brand, Udyam certificate (if MSME)'),
  ('IEC', 'PAN card, Aadhaar card, business address proof, cancelled cheque or bank certificate, passport-size photo'),
  ('FSSAI', 'Photo ID (Aadhaar or PAN), passport-size photo, business address proof, rent agreement or owner NOC, list of food products'),
  ('HUID / Hallmarking', 'GST certificate, PAN card, Aadhaar card, shop address proof, passport-size photo of the owner'),
  ('Company Registration', 'PAN and Aadhaar of all directors, passport-size photos, office address proof with owner NOC, 2-3 proposed company names'),
  ('LLP Registration', 'PAN and Aadhaar of all partners, passport-size photos, office address proof with owner NOC, 2-3 proposed LLP names'),
  ('MSME / Udyam', 'Aadhaar card, PAN card, bank account details, business address and activity details'),
  ('Income Tax', 'PAN card, Aadhaar card, Form 16 or income details, bank statements, investment and deduction proofs'),
  ('Accounting', 'Bank statements, sales and purchase bills, expense bills, previous returns')
) as d(name, docs)
where o.name = d.name and o.documents = '';

-- 5. Settings -------------------------------------------------------------------------
insert into private.app_settings (key, value) values ('upi_id', ''), ('service_owner_map', '{}')
on conflict (key) do nothing;

create or replace function public.get_app_settings()
returns jsonb language sql stable security definer set search_path to '' as $$
  select case when private.is_admin() then
    (select jsonb_object_agg(key, value) from private.app_settings
     where key in ('upi_id', 'service_owner_map', 'whatsapp_lead_owner'))
  else '{}'::jsonb end
$$;
revoke all on function public.get_app_settings() from public, anon;
grant execute on function public.get_app_settings() to authenticated;

create or replace function public.set_app_setting(p_key text, p_value text)
returns void language plpgsql security definer set search_path to '' as $$
begin
  if not private.is_super_admin() then raise exception 'Only the Super Admin can change settings'; end if;
  if p_key not in ('upi_id', 'service_owner_map') then raise exception 'Unknown setting'; end if;
  if p_key = 'service_owner_map' then perform p_value::jsonb; end if; -- must be valid JSON
  insert into private.app_settings (key, value, updated_at) values (p_key, coalesce(p_value, ''), now())
  on conflict (key) do update set value = excluded.value, updated_at = now();
end $$;
revoke all on function public.set_app_setting(text, text) from public, anon;
grant execute on function public.set_app_setting(text, text) to authenticated;

-- 6. Owner for auto-created leads -------------------------------------------------------
create or replace function public.lead_owner_for_services(p_services text[])
returns uuid language plpgsql stable security definer set search_path to '' as $$
declare v_map jsonb; v_s text; v_id uuid;
begin
  begin v_map := (select value from private.app_settings where key = 'service_owner_map')::jsonb;
  exception when others then v_map := '{}'::jsonb; end;
  foreach v_s in array coalesce(p_services, '{}'::text[]) loop
    v_id := nullif(v_map ->> v_s, '')::uuid;
    if v_id is not null and exists (select 1 from public.user_roles where user_id = v_id) then return v_id; end if;
  end loop;
  return (select nullif(value, '')::uuid from private.app_settings where key = 'whatsapp_lead_owner');
end $$;
revoke all on function public.lead_owner_for_services(text[]) from public, anon;
grant execute on function public.lead_owner_for_services(text[]) to authenticated, service_role;

-- 7. Document checklist when Verified ---------------------------------------------------
create or replace function private.wa_doc_checklist() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_docs text; v_services text;
begin
  if new.stage = 'Verified' and old.stage is distinct from 'Verified'
     and new.whatsapp_opt_in and coalesce(array_length(new.lead_types, 1), 0) > 0 then
    select string_agg(o.name || ': ' || o.documents, '; ' order by o.sort_order), string_agg(o.name, ', ' order by o.sort_order)
      into v_docs, v_services
    from public.lead_type_options o
    where o.name = any(new.lead_types) and o.documents <> '';
    if v_docs is not null then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C-docs', 'lw_c_documents',
        jsonb_build_array(new.name, v_services, left(v_docs, 700)), 'CD:' || new.id, now() + interval '10 minutes');
    end if;
  end if;
  return new;
end $$;
drop trigger if exists wa_doc_checklist on public.leads;
create trigger wa_doc_checklist after update on public.leads
  for each row execute function private.wa_doc_checklist();

-- 8. Payment reminders ------------------------------------------------------------------
create or replace function private.wa_payment_reminders() returns integer
language plpgsql security definer set search_path = '' as $$
declare v_upi text := (select value from private.app_settings where key = 'upi_id'); v_n int := 0; r record;
  v_today date := (now() at time zone 'Asia/Kolkata')::date;
begin
  if coalesce(v_upi, '') = '' then return 0; end if;
  for r in
    select l.* from public.leads l
    where l.stage = 'Work done' and l.payment_status = 'pending' and coalesce(l.pending_payment, 0) > 0
      and l.whatsapp_opt_in
      and (select count(*) from public.whatsapp_messages m where m.lead_id = l.id and m.message_key = 'C-pay') < 5
      and not exists (select 1 from public.whatsapp_messages m where m.lead_id = l.id and m.message_key = 'C-pay'
                      and m.created_at > now() - interval '70 hours')
  loop
    perform private.wa_enqueue(r.id, r.phone, 'client', null, 'C-pay', 'lw_c_payment_reminder',
      jsonb_build_array(r.name, to_char(r.pending_payment, 'FM99,99,99,990.00'),
        coalesce(nullif(array_to_string(r.lead_types, ', '), ''), 'your work'), v_upi),
      'PR:' || r.id || ':' || v_today);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;

select cron.unschedule('whatsapp-payment-reminders') where exists (select 1 from cron.job where jobname = 'whatsapp-payment-reminders');
select cron.schedule('whatsapp-payment-reminders', '45 5 * * 1-6', $$select private.wa_payment_reminders()$$);
