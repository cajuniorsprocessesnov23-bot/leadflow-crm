-- WhatsApp message queue: the CRM decides WHICH message goes to WHOM and WHEN.
-- Nothing is sent by this migration. It only adds rows with status 'queued' to
-- public.whatsapp_messages; the whatsapp-dispatch Edge Function sends them (quiet hours
-- 9 AM–8 PM IST, templates approved by Meta, consent checked again at send time).
--
-- Adds:
--   1. private.app_settings      key/value settings (Super Admin WhatsApp number, launch time)
--   2. private.wa_phone()        normalise a phone number to 91XXXXXXXXXX
--   3. private.wa_enqueue()      insert one queued message (never twice: dedupe_key)
--   4. trigger wa_lead_events    on leads: C1 lead added, T1 new lead to RM, C2 missed call
--                                (once per day), C3 last attempt, C4 verified, C5 group made +
--                                work-assigned to executor, C6 work processed, C7 work done,
--                                C12 documents dispatched, C14 work on hold (+1 day),
--                                T6 work dropped to Super Admin.
-- Old leads: only events that happen after this migration are queued (no backlog).
-- Impact on existing data: none (no existing rows are changed).

create table if not exists private.app_settings (
  key text primary key,
  value text not null default '',
  updated_at timestamptz not null default now()
);
insert into private.app_settings (key, value) values
  ('super_admin_whatsapp', '918208221425'),
  ('whatsapp_launch_at', now()::text)
on conflict (key) do nothing;

create or replace function private.wa_phone(p text) returns text
language sql immutable as $$
  select case
    when d is null or d = '' then null
    when length(d) = 10 then '91' || d
    when length(d) = 12 and left(d, 2) = '91' then d
    when length(d) between 11 and 15 then d
    else null end
  from (select regexp_replace(coalesce(p, ''), '\D', '', 'g') as d) x
$$;

create or replace function private.wa_enqueue(
  p_lead_id text, p_phone text, p_kind text, p_user uuid, p_key text, p_template text,
  p_params jsonb, p_dedupe text, p_when timestamptz default now()
) returns void
language plpgsql security definer set search_path = '' as $$
declare v_phone text := private.wa_phone(p_phone);
begin
  if v_phone is null then return; end if;
  insert into public.whatsapp_messages
    (lead_id, recipient_phone, recipient_kind, recipient_user_id, message_key, template_name, params, dedupe_key, scheduled_for, created_by)
  values (p_lead_id, v_phone, p_kind, p_user, p_key, p_template, coalesce(p_params, '{}'::jsonb), p_dedupe, p_when, auth.uid())
  on conflict (dedupe_key) do nothing;
end $$;

create or replace function private.wa_staff_name(p_user uuid) returns text
language sql stable security definer set search_path = '' as $$
  select coalesce(nullif(u.raw_user_meta_data ->> 'full_name', ''), split_part(u.email, '@', 1), 'our team')
  from auth.users u where u.id = p_user
$$;

create or replace function private.wa_staff_phone(p_user uuid) returns text
language sql stable security definer set search_path = '' as $$
  select nullif(r.whatsapp_number, '') from public.user_roles r where r.user_id = p_user
$$;

create or replace function private.wa_lead_events() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
  v_services text := coalesce(nullif(array_to_string(new.lead_types, ', '), ''), 'your requirement');
  v_rm uuid := coalesce(new.owner_user_id, new.created_by);
  v_rm_name text := private.wa_staff_name(coalesce(new.owner_user_id, new.created_by));
  v_ref text := coalesce(nullif(new.lead_code, ''), new.id);
  v_file text := coalesce(nullif(new.group_number, ''), v_ref);
  v_client boolean := new.whatsapp_opt_in and coalesce(new.stage, '') not in ('False lead', 'Clear no lead');
  v_admin text := (select value from private.app_settings where key = 'super_admin_whatsapp');
  v_attempt int;
begin
  if tg_op = 'INSERT' then
    if v_client then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C1', 'lw_c1_lead_added',
        jsonb_build_array(new.name, v_services, v_ref), 'C1:' || new.id);
    end if;
    perform private.wa_enqueue(new.id, private.wa_staff_phone(v_rm), 'staff', v_rm, 'T1', 'lw_t1_new_lead',
      jsonb_build_array(v_ref, new.name, new.phone, v_services, coalesce(nullif(new.source, ''), 'CRM')), 'T1:' || new.id);
    return new;
  end if;

  -- UPDATE: react only to real changes.
  if new.stage is distinct from old.stage and v_client then
    if new.stage like 'Not picked %' then
      v_attempt := nullif(regexp_replace(new.stage, '\D', '', 'g'), '')::int;
      if v_attempt between 1 and 4 then
        perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C2', 'lw_c2_missed_call',
          jsonb_build_array(new.name, v_services), 'C2:' || new.id || ':' || (now() at time zone 'Asia/Kolkata')::date);
      elsif v_attempt = 5 then
        perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C3', 'lw_c3_last_attempt',
          jsonb_build_array(new.name, v_services), 'C3:' || new.id);
      end if;
    elsif new.stage = 'Verified' then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C4', 'lw_c4_verified',
        jsonb_build_array(new.name, v_services, v_rm_name), 'C4:' || new.id);
    elsif new.stage = 'Group made' then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C5', 'lw_c5_group_made',
        jsonb_build_array(new.name, v_services, v_file), 'C5:' || new.id);
    elsif new.stage = 'Work processed' then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C6', 'lw_c6_work_processed',
        jsonb_build_array(v_file, v_services), 'C6:' || new.id);
    elsif new.stage = 'Work done' then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C7', 'lw_c7_work_done',
        jsonb_build_array(v_services, v_file), 'C7:' || new.id);
    elsif new.stage = 'Work dropped' then
      perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C14', 'lw_c14_work_on_hold',
        jsonb_build_array(new.name, v_services), 'C14:' || new.id || ':' || coalesce(new.dropped_date::text, now()::date::text),
        now() + interval '1 day');
    end if;
  end if;

  if new.stage is distinct from old.stage and new.stage = 'Work dropped' then
    perform private.wa_enqueue(new.id, v_admin, 'super_admin', null, 'T6', 'lw_t6_work_dropped',
      jsonb_build_array(private.wa_staff_name(coalesce(auth.uid(), v_rm)), new.name, v_ref, v_services, coalesce(nullif(left(new.notes, 120), ''), '-')),
      'T6:' || new.id || ':' || now()::date);
  end if;

  -- Work Executor assigned (or changed): tell the executor.
  if new.executor_user_id is not null and new.executor_user_id is distinct from old.executor_user_id then
    perform private.wa_enqueue(new.id, private.wa_staff_phone(new.executor_user_id), 'staff', new.executor_user_id, 'T-assign', 'lw_t_work_assigned',
      jsonb_build_array(private.wa_staff_name(new.executor_user_id), v_rm_name, new.name, v_file, v_services,
        coalesce(to_char(new.work_due_date, 'DD Mon'), 'the due date')),
      'TA:' || new.id || ':' || new.executor_user_id);
  end if;

  -- Documents dispatched ticked, with courier details.
  if coalesce(new.documents_dispatched, false) and not coalesce(old.documents_dispatched, false) and v_client then
    perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C12', 'lw_c12_docs_dispatched',
      jsonb_build_array(new.name, v_services, coalesce(nullif(new.courier_name, ''), 'courier'),
        coalesce(nullif(new.tracking_id, ''), '-'), coalesce(nullif(new.tracking_link, ''), '-')),
      'C12:' || new.id);
  end if;

  return new;
end $$;

drop trigger if exists wa_lead_events on public.leads;
create trigger wa_lead_events after insert or update on public.leads
  for each row execute function private.wa_lead_events();

-- Opting out or being marked a non-lead cancels anything still waiting for that client.
create or replace function private.wa_cancel_on_optout() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if (not new.whatsapp_opt_in and old.whatsapp_opt_in) or (new.stage in ('False lead', 'Clear no lead') and new.stage is distinct from old.stage) then
    update public.whatsapp_messages set status = 'skipped', error_detail = 'Client opted out or not a lead'
    where lead_id = new.id and recipient_kind = 'client' and status = 'queued';
  end if;
  return new;
end $$;
drop trigger if exists wa_cancel_on_optout on public.leads;
create trigger wa_cancel_on_optout after update on public.leads
  for each row execute function private.wa_cancel_on_optout();
