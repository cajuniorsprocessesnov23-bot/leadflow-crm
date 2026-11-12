-- LeadFlow CRM – phase 1: two-person workflow + WhatsApp automation foundations
-- Decisions (Kunal, 13 Nov 2026):
--   * Each lead has a Relationship Manager (owner_user_id, already exists) and,
--     from "Group made", a Work Executor picked by the RM. After "Work done" the
--     lead is the RM's again. Collections/commission stay with the RM.
--   * WhatsApp consent is ON by default; removed when the client says no / STOP.
--   * Work delay = a service's target days passed without "Work done".
--   * Portal credentials stay plain text; Drive links for raw + completed docs.
--
-- What this migration does (no existing row is deleted or overwritten except
-- the consent flag, see 2):
--   1. leads: executor_user_id, work_assigned_at, work_due_date, callback_due_at,
--      callback_note, WhatsApp opt-out fields, courier/tracking fields.
--   2. Consent on by default; existing 80 leads switched to consent = true.
--      (They only get messages for NEW events after launch – enforced in code.)
--   3. lead_type_options.target_days (work deadline per service).
--   4. user_roles.whatsapp_number (staff number for team messages).
--   5. client_drive_links: raw_docs_url, completed_docs_url.
--   6. whatsapp_messages: outbox + log (queued/sent/delivered/read/failed), never
--      sends the same message twice (dedupe_key).
--   7. whatsapp_inbound: client replies, button taps, STOP.
--   8. Access: the Work Executor can see/edit the leads assigned to them; only the
--      RM or an admin may pick/change the executor.

begin;

-- 1. Lead fields --------------------------------------------------------------
alter table public.leads
  add column if not exists executor_user_id uuid references auth.users(id) on delete set null,
  add column if not exists work_assigned_at timestamptz,
  add column if not exists work_due_date date,
  add column if not exists callback_due_at timestamptz,
  add column if not exists callback_note text not null default '',
  add column if not exists whatsapp_opted_out_at timestamptz,
  add column if not exists whatsapp_optout_reason text not null default '',
  add column if not exists courier_name text not null default '',
  add column if not exists tracking_id text not null default '',
  add column if not exists tracking_link text not null default '';
create index if not exists leads_executor_user_id_idx on public.leads (executor_user_id);
create index if not exists leads_callback_due_at_idx on public.leads (callback_due_at) where callback_due_at is not null;

-- 2. Consent on by default ------------------------------------------------------
alter table public.leads alter column whatsapp_opt_in set default true;
update public.leads set whatsapp_opt_in = true where whatsapp_opt_in = false and whatsapp_opted_out_at is null;

-- 3. Target days per service ------------------------------------------------------
alter table public.lead_type_options add column if not exists target_days integer check (target_days is null or target_days between 1 and 365);

-- 4. Staff WhatsApp number --------------------------------------------------------
alter table public.user_roles add column if not exists whatsapp_number text not null default '';

-- 5. Document folders -------------------------------------------------------------
alter table public.client_drive_links
  add column if not exists raw_docs_url text not null default '',
  add column if not exists completed_docs_url text not null default '';

-- 6. Outbox + log -------------------------------------------------------------------
create table if not exists public.whatsapp_messages (
  id uuid primary key default gen_random_uuid(),
  lead_id text references public.leads(id) on delete set null,
  recipient_phone text not null,
  recipient_kind text not null check (recipient_kind in ('client', 'staff', 'admin', 'super_admin', 'test')),
  recipient_user_id uuid references auth.users(id) on delete set null,
  message_key text not null,                -- C1, C2 … T1 … R1 …
  template_name text not null default '',
  params jsonb not null default '{}'::jsonb,
  dedupe_key text unique,                   -- same key never sent twice
  status text not null default 'queued' check (status in ('queued', 'sending', 'sent', 'delivered', 'read', 'failed', 'skipped')),
  scheduled_for timestamptz not null default now(),
  wamid text unique,
  error_code text not null default '',
  error_detail text not null default '',
  attempts integer not null default 0,
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  delivered_at timestamptz,
  read_at timestamptz,
  failed_at timestamptz
);
create index if not exists whatsapp_messages_due_idx on public.whatsapp_messages (scheduled_for) where status = 'queued';
create index if not exists whatsapp_messages_lead_idx on public.whatsapp_messages (lead_id, created_at desc);

-- 7. Inbound -------------------------------------------------------------------------
create table if not exists public.whatsapp_inbound (
  id uuid primary key default gen_random_uuid(),
  wamid text unique,
  from_phone text not null,
  lead_id text references public.leads(id) on delete set null,
  message_type text not null default '',
  body text not null default '',
  button_payload text not null default '',
  context_wamid text not null default '',  -- which of our messages they replied to
  raw jsonb not null default '{}'::jsonb,
  received_at timestamptz not null default now(),
  processed_at timestamptz,
  action_taken text not null default ''
);
create index if not exists whatsapp_inbound_lead_idx on public.whatsapp_inbound (lead_id, received_at desc);

alter table public.whatsapp_messages enable row level security;
alter table public.whatsapp_inbound enable row level security;
-- Read-only for people who can see the lead (admins see all). Writes only by the
-- server functions (service role) – no insert/update/delete policies.
create policy whatsapp_messages_select on public.whatsapp_messages for select to authenticated
  using ((select private.is_admin()) or (lead_id is not null and private.can_access_lead(lead_id)) or recipient_user_id = (select auth.uid()));
create policy whatsapp_inbound_select on public.whatsapp_inbound for select to authenticated
  using ((select private.is_admin()) or (lead_id is not null and private.can_access_lead(lead_id)));

-- 8. Access for the Work Executor ---------------------------------------------------
create or replace function private.can_access_lead(p_lead_id text)
returns boolean language sql stable security definer set search_path to '' as $$
  select private.is_admin() or exists (
    select 1 from public.leads l
    where l.id = p_lead_id
      and (l.created_by = (select auth.uid()) or l.owner_user_id = (select auth.uid()) or l.executor_user_id = (select auth.uid())));
$$;

drop policy if exists "Users can view own leads and admins can view all" on public.leads;
create policy "Users can view own leads and admins can view all" on public.leads
  for select to authenticated
  using (created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or executor_user_id = (select auth.uid()) or (select private.is_admin()));

drop policy if exists "Users can edit own leads and admins can edit all" on public.leads;
create policy "Users can edit own leads and admins can edit all" on public.leads
  for update to authenticated
  using ((created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or executor_user_id = (select auth.uid()) or (select private.is_admin()))
         and (select private.has_permission('leads_edit')))
  with check (created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or executor_user_id = (select auth.uid()) or (select private.is_admin()));

-- Owner (RM) changes: admins only (unchanged). Executor: the RM or an admin.
create or replace function private.guard_lead_owner()
returns trigger language plpgsql security definer set search_path to '' as $$
declare v_existing public.leads%rowtype;
begin
  if auth.uid() is null or private.is_admin() then
    if tg_op = 'UPDATE' and new.executor_user_id is distinct from old.executor_user_id and new.executor_user_id is not null then
      new.work_assigned_at := now();
    end if;
    return new;
  end if;
  if tg_op = 'INSERT' then
    select * into v_existing from public.leads l where l.id = new.id;
    if found then
      -- An upsert of an existing lead: keep its RM and executor unless the RM is changing the executor.
      new.owner_user_id := v_existing.owner_user_id;
      if new.executor_user_id is distinct from v_existing.executor_user_id
         and coalesce(v_existing.owner_user_id, v_existing.created_by) is distinct from auth.uid() then
        new.executor_user_id := v_existing.executor_user_id;
      elsif new.executor_user_id is distinct from v_existing.executor_user_id and new.executor_user_id is not null then
        new.work_assigned_at := now();
      end if;
    else
      new.owner_user_id := auth.uid();
    end if;
  else
    if new.owner_user_id is distinct from old.owner_user_id then
      raise exception 'Only Admin or Super Admin can change the Relationship Manager.';
    end if;
    if new.executor_user_id is distinct from old.executor_user_id then
      if coalesce(old.owner_user_id, old.created_by) is distinct from auth.uid() then
        raise exception 'Only the Relationship Manager or an admin can choose the Work Executor.';
      end if;
      if new.executor_user_id is not null then new.work_assigned_at := now(); end if;
    end if;
  end if;
  return new;
end;
$$;

-- Work due date = assignment day + the longest target days of the lead's services.
create or replace function private.set_work_due_date()
returns trigger language plpgsql security definer set search_path to '' as $$
declare v_days integer;
begin
  if new.executor_user_id is not null and (tg_op = 'INSERT' or new.executor_user_id is distinct from old.executor_user_id or new.work_due_date is null) then
    select max(o.target_days) into v_days from public.lead_type_options o where o.name = any(coalesce(new.lead_types, '{}'::text[]));
    new.work_due_date := case when v_days is null then null else (coalesce(new.work_assigned_at, now()) at time zone 'Asia/Kolkata')::date + v_days end;
  end if;
  return new;
end;
$$;
drop trigger if exists set_work_due_date on public.leads;
create trigger set_work_due_date before insert or update on public.leads
  for each row execute function private.set_work_due_date();

-- Team list now also says who has a WhatsApp number (not the number itself).
drop function if exists public.list_team_members();
create function public.list_team_members()
returns table (user_id uuid, full_name text, role text, has_whatsapp boolean)
language sql stable security definer set search_path to '' as $$
  select r.user_id,
         coalesce(u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1)) as full_name,
         r.role,
         coalesce(r.whatsapp_number, '') <> '' as has_whatsapp
  from public.user_roles r join auth.users u on u.id = r.user_id
  where (select auth.uid()) is not null
  order by 2;
$$;
revoke all on function public.list_team_members() from public, anon;
grant execute on function public.list_team_members() to authenticated;

commit;
