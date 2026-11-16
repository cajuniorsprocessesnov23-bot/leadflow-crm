-- Sales flow, change log and targets (16 Nov 2026)
-- What this adds (all additive):
--   1. leads.quoted_fee (numeric, default 0): the price quoted to the client.
--   2. leads.lost_reason (text): why a lead was marked False lead / Clear no lead / Work dropped.
--   3. set_my_whatsapp(number): each user can save their own WhatsApp number (for team alerts).
--   4. lead_events: change log. A trigger records who changed stage, owner, executor, service,
--      source, quoted fee, payment status or pending amount, and when. Readable by anyone who
--      can see the lead; nobody can edit or delete entries from the app.
--   5. staff_targets: monthly targets per person (calls, conversions, collection). Everyone
--      can read their own; Admins read and set all.
--   6. Setting google_review_link (empty) for the review-request message.
-- Impact on existing data: two new empty columns on leads; no rows changed.

alter table public.leads add column if not exists quoted_fee numeric not null default 0;
alter table public.leads add column if not exists lost_reason text not null default '';

-- 3. Own WhatsApp number --------------------------------------------------------------
create or replace function public.set_my_whatsapp(p_number text)
returns text language plpgsql security definer set search_path to '' as $$
declare v text := regexp_replace(coalesce(p_number, ''), '\D', '', 'g');
begin
  if auth.uid() is null then raise exception 'Not signed in'; end if;
  if length(v) = 10 then v := '91' || v; end if;
  if v !~ '^91[6-9][0-9]{9}$' then raise exception 'Enter a valid 10-digit Indian mobile number'; end if;
  update public.user_roles set whatsapp_number = v where user_id = auth.uid();
  return v;
end $$;
revoke all on function public.set_my_whatsapp(text) from public, anon;
grant execute on function public.set_my_whatsapp(text) to authenticated;

-- 4. Change log -------------------------------------------------------------------------
create table if not exists public.lead_events (
  id bigint generated always as identity primary key,
  lead_id text not null,
  changed_at timestamptz not null default now(),
  changed_by uuid,
  changed_by_name text not null default '',
  field text not null,
  old_value text not null default '',
  new_value text not null default ''
);
create index if not exists lead_events_lead_idx on public.lead_events (lead_id, changed_at desc);
alter table public.lead_events enable row level security;
drop policy if exists lead_events_select on public.lead_events;
create policy lead_events_select on public.lead_events for select to authenticated
  using (private.can_access_lead(lead_id));

create or replace function private.log_lead_changes() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_by uuid := auth.uid(); v_name text := coalesce(private.wa_staff_name(auth.uid()), 'System');
begin
  if auth.uid() is null then v_name := 'System (WhatsApp / website)'; end if;
  if new.stage is distinct from old.stage then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Stage', coalesce(old.stage, ''), coalesce(new.stage, '')); end if;
  if new.owner_user_id is distinct from old.owner_user_id then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Owner', coalesce(private.wa_staff_name(old.owner_user_id), ''), coalesce(private.wa_staff_name(new.owner_user_id), '')); end if;
  if new.executor_user_id is distinct from old.executor_user_id then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Work Executor', coalesce(private.wa_staff_name(old.executor_user_id), ''), coalesce(private.wa_staff_name(new.executor_user_id), '')); end if;
  if new.lead_types is distinct from old.lead_types then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Service', array_to_string(old.lead_types, ', '), array_to_string(new.lead_types, ', ')); end if;
  if new.source is distinct from old.source then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Source', coalesce(old.source, ''), coalesce(new.source, '')); end if;
  if new.quoted_fee is distinct from old.quoted_fee then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Quoted fee', old.quoted_fee::text, new.quoted_fee::text); end if;
  if new.payment_status is distinct from old.payment_status or new.pending_payment is distinct from old.pending_payment then
    insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
    values (new.id, v_by, v_name, 'Payment', coalesce(old.payment_status, '') || ' ₹' || coalesce(old.pending_payment, 0),
            coalesce(new.payment_status, '') || ' ₹' || coalesce(new.pending_payment, 0)); end if;
  return new;
end $$;
drop trigger if exists log_lead_changes on public.leads;
create trigger log_lead_changes after update on public.leads
  for each row execute function private.log_lead_changes();

create or replace function private.log_lead_created() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.lead_events (lead_id, changed_by, changed_by_name, field, old_value, new_value)
  values (new.id, auth.uid(), coalesce(private.wa_staff_name(auth.uid()), 'System (WhatsApp / website)'), 'Created', '',
          coalesce(nullif(new.source, ''), 'CRM'));
  return new;
end $$;
drop trigger if exists log_lead_created on public.leads;
create trigger log_lead_created after insert on public.leads
  for each row execute function private.log_lead_created();

-- 5. Targets ----------------------------------------------------------------------------
create table if not exists public.staff_targets (
  user_id uuid not null references auth.users(id) on delete cascade,
  month date not null,
  calls int not null default 0,
  conversions int not null default 0,
  collection numeric not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_id, month)
);
alter table public.staff_targets enable row level security;
drop policy if exists staff_targets_select on public.staff_targets;
create policy staff_targets_select on public.staff_targets for select to authenticated
  using (user_id = (select auth.uid()) or (select private.is_admin()));
drop policy if exists staff_targets_write on public.staff_targets;
create policy staff_targets_write on public.staff_targets for all to authenticated
  using ((select private.is_admin())) with check ((select private.is_admin()));

-- 6. Review link setting ------------------------------------------------------------------
insert into private.app_settings (key, value) values ('google_review_link', '') on conflict (key) do nothing;
create or replace function public.get_app_settings()
returns jsonb language sql stable security definer set search_path to '' as $$
  select case when private.is_admin() then
    (select jsonb_object_agg(key, value) from private.app_settings
     where key in ('upi_id', 'service_owner_map', 'whatsapp_lead_owner', 'google_review_link'))
  else '{}'::jsonb end
$$;
create or replace function public.set_app_setting(p_key text, p_value text)
returns void language plpgsql security definer set search_path to '' as $$
begin
  if not private.is_super_admin() then raise exception 'Only the Super Admin can change settings'; end if;
  if p_key not in ('upi_id', 'service_owner_map', 'google_review_link') then raise exception 'Unknown setting'; end if;
  if p_key = 'service_owner_map' then perform p_value::jsonb; end if;
  if p_key = 'google_review_link' and p_value <> '' and p_value !~ '^https://' then raise exception 'Review link must start with https://'; end if;
  insert into private.app_settings (key, value, updated_at) values (p_key, coalesce(p_value, ''), now())
  on conflict (key) do update set value = excluded.value, updated_at = now();
end $$;
