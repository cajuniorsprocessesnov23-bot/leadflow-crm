-- LeadFlow CRM – owner-based attribution + safe payment recording
-- Decisions (owner, 2026-11-12):
--   * Staff credit for collections & commission = the lead's ASSIGNED OWNER.
--   * Existing leads: owner = the user who created them.
--   * Recorded payments can be edited/deleted only by Admin / Super Admin.
--
-- What this migration does
--   1. Data-loss guards: deleting a user no longer deletes their leads;
--      deleting a lead that has payments is blocked.
--   2. Adds leads.owner_user_id (+ backfill from created_by).
--   3. Adds payment_collections.credited_user_id / credited_user_name.
--   4. private.can_access_lead(): creator OR assigned owner OR admin.
--   5. Owner can be changed only by Admin / Super Admin (trigger).
--   6. public.record_payment(): one transaction that checks the balance,
--      inserts the collection, computes commission from the OWNER's rate
--      (professional fees only) and updates the lead's balances.
--   7. Payment rows: staff can no longer insert/update/delete directly;
--      inserts go through record_payment(), edits/deletes are admin-only.
--   8. public.list_team_members(): names for the "Assigned owner" dropdown.
-- Existing data: 80 leads get owner_user_id; 0 payment rows exist.

begin;

-- 1. Data-loss guards ---------------------------------------------------------
alter table public.leads alter column created_by drop not null;
alter table public.leads drop constraint leads_created_by_fkey;
alter table public.leads add constraint leads_created_by_fkey
  foreign key (created_by) references auth.users(id) on delete set null;

-- Payment history must survive deleting the user who recorded it (name stays in created_by_name).
alter table public.payment_collections drop constraint payment_collections_created_by_fkey;
alter table public.payment_collections add constraint payment_collections_created_by_fkey
  foreign key (created_by) references auth.users(id) on delete set null;

alter table public.payment_collections drop constraint payment_collections_lead_id_fkey;
alter table public.payment_collections add constraint payment_collections_lead_id_fkey
  foreign key (lead_id) references public.leads(id) on delete restrict;

-- 2. Assigned owner -------------------------------------------------------------
alter table public.leads
  add column if not exists owner_user_id uuid references auth.users(id) on delete set null;
alter table public.leads alter column owner_user_id set default auth.uid();
create index if not exists leads_owner_user_id_idx on public.leads (owner_user_id);

update public.leads l
set owner_user_id = l.created_by,
    owner = coalesce(nullif(l.owner, ''), nullif(l.created_by_name, ''),
                     (select coalesce(u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1))
                      from auth.users u where u.id = l.created_by), '')
where l.owner_user_id is null and l.created_by is not null;

-- 3. Credited staff on collections ---------------------------------------------
alter table public.payment_collections
  add column if not exists credited_user_id uuid references auth.users(id) on delete set null,
  add column if not exists credited_user_name text not null default '';
create index if not exists payment_collections_credited_user_id_idx on public.payment_collections (credited_user_id);
create index if not exists payment_collections_collected_on_idx on public.payment_collections (collected_on);

update public.payment_collections p
set credited_user_id = coalesce(l.owner_user_id, p.created_by),
    credited_user_name = coalesce(nullif(l.owner, ''), p.created_by_name, '')
from public.leads l
where l.id = p.lead_id and p.credited_user_id is null;

-- 4. Access helpers ---------------------------------------------------------------
create or replace function private.is_admin()
returns boolean language sql stable security definer set search_path to '' as $$
  select exists (select 1 from public.user_roles r
                 where r.user_id = (select auth.uid()) and r.role in ('admin', 'super_admin'));
$$;

create or replace function private.can_access_lead(p_lead_id text)
returns boolean language sql stable security definer set search_path to '' as $$
  select private.is_admin() or exists (
    select 1 from public.leads l
    where l.id = p_lead_id
      and (l.created_by = (select auth.uid()) or l.owner_user_id = (select auth.uid())));
$$;

create or replace function private.has_permission(p_key text)
returns boolean language sql stable security definer set search_path to '' as $$
  select exists (select 1 from public.user_roles r
                 where r.user_id = (select auth.uid())
                   and (r.role = 'super_admin' or coalesce((r.permissions ->> p_key)::boolean, false)));
$$;

-- 5. Only admins may assign / reassign owners ------------------------------------
create or replace function private.guard_lead_owner()
returns trigger language plpgsql security definer set search_path to '' as $$
begin
  if auth.uid() is null or private.is_admin() then
    return new;                                   -- service role / SQL editor / admins
  end if;
  if tg_op = 'INSERT' then
    -- An upsert of an existing lead arrives here as INSERT first: keep its current owner.
    -- A genuinely new lead created by staff belongs to that staff member.
    select l.owner_user_id into new.owner_user_id from public.leads l where l.id = new.id;
    if not found then
      new.owner_user_id := auth.uid();
    end if;
  elsif new.owner_user_id is distinct from old.owner_user_id then
    raise exception 'Only Admin or Super Admin can change the assigned owner.';
  end if;
  return new;
end;
$$;
drop trigger if exists guard_lead_owner on public.leads;
create trigger guard_lead_owner before insert or update on public.leads
  for each row execute function private.guard_lead_owner();

-- 6. Policies: owners get the same access as creators ----------------------------
drop policy if exists "Users can view own leads and admins can view all" on public.leads;
create policy "Users can view own leads and admins can view all" on public.leads
  for select to authenticated
  using (created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or (select private.is_admin()));

drop policy if exists "Users can edit own leads and admins can edit all" on public.leads;
create policy "Users can edit own leads and admins can edit all" on public.leads
  for update to authenticated
  using ((created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or (select private.is_admin()))
         and (select private.has_permission('leads_edit')))
  with check (created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or (select private.is_admin()));

drop policy if exists "Users can delete own leads and admins can delete all" on public.leads;
create policy "Users can delete own leads and admins can delete all" on public.leads
  for delete to authenticated
  using ((created_by = (select auth.uid()) or owner_user_id = (select auth.uid()) or (select private.is_admin()))
         and (select private.has_permission('leads_delete')));

-- payment_collections
drop policy if exists payment_collections_select_owned on public.payment_collections;
drop policy if exists payment_collections_insert_owned on public.payment_collections;
drop policy if exists payment_collections_update_owned on public.payment_collections;
drop policy if exists payment_collections_delete_owned on public.payment_collections;
create policy payment_collections_select on public.payment_collections
  for select to authenticated using (private.can_access_lead(lead_id));
create policy payment_collections_update_admin on public.payment_collections
  for update to authenticated using ((select private.is_admin())) with check ((select private.is_admin()));
create policy payment_collections_delete_admin on public.payment_collections
  for delete to authenticated using ((select private.is_admin()));
-- (no INSERT policy: new payments are recorded only via public.record_payment)

-- call_activity / portals / drive links: include assigned owner
drop policy if exists call_activity_insert_own_lead on public.call_activity;
create policy call_activity_insert_own_lead on public.call_activity
  for insert to authenticated
  with check (staff_user_id = (select auth.uid()) and private.can_access_lead(lead_id));

drop policy if exists client_portals_select_by_lead_owner on public.client_portal_credentials;
drop policy if exists client_portals_insert_by_lead_owner on public.client_portal_credentials;
drop policy if exists client_portals_update_by_lead_owner on public.client_portal_credentials;
drop policy if exists client_portals_delete_by_lead_owner on public.client_portal_credentials;
create policy client_portals_select_by_lead_owner on public.client_portal_credentials
  for select to authenticated using (private.can_access_lead(lead_id));
create policy client_portals_insert_by_lead_owner on public.client_portal_credentials
  for insert to authenticated with check (created_by = (select auth.uid()) and private.can_access_lead(lead_id));
create policy client_portals_update_by_lead_owner on public.client_portal_credentials
  for update to authenticated using (private.can_access_lead(lead_id)) with check (private.can_access_lead(lead_id));
create policy client_portals_delete_by_lead_owner on public.client_portal_credentials
  for delete to authenticated using (private.can_access_lead(lead_id));

drop policy if exists client_drive_links_by_lead_owner on public.client_drive_links;
create policy client_drive_links_by_lead_owner on public.client_drive_links
  for all to authenticated using (private.can_access_lead(lead_id)) with check (private.can_access_lead(lead_id));

-- 7. Atomic payment recording ----------------------------------------------------
create or replace function public.record_payment(
  p_lead_id text,
  p_component text,
  p_amount numeric,
  p_collected_on date default null
) returns jsonb
language plpgsql security definer set search_path to '' as $$
declare
  v_uid uuid := auth.uid();
  v_today date := (now() at time zone 'Asia/Kolkata')::date;
  v_on date := coalesce(p_collected_on, (now() at time zone 'Asia/Kolkata')::date);
  v_lead public.leads%rowtype;
  v_balance numeric;
  v_credited uuid;
  v_credited_name text;
  v_recorder_name text;
  v_rate numeric := 0;
  v_row public.payment_collections%rowtype;
  v_gov numeric;
  v_prof numeric;
  v_pending numeric;
begin
  if v_uid is null then raise exception 'Not signed in.'; end if;
  if not private.has_permission('leads_edit') and not private.is_admin() then
    raise exception 'You do not have permission to record payments.';
  end if;
  if p_component not in ('government_charges', 'professional_fees') then
    raise exception 'Payment component must be government_charges or professional_fees.';
  end if;
  if p_amount is null or p_amount <= 0 then raise exception 'Enter an amount greater than zero.'; end if;
  if v_on > v_today then raise exception 'Collection date cannot be in the future.'; end if;
  if v_on <> v_today and not private.is_admin() then
    raise exception 'Only Admin or Super Admin can record a payment for an earlier date.';
  end if;

  select * into v_lead from public.leads where id = p_lead_id for update;
  if not found then raise exception 'Client not found.'; end if;
  if not private.can_access_lead(p_lead_id) then raise exception 'You cannot record payments for this client.'; end if;

  v_balance := case when p_component = 'government_charges'
                    then coalesce(v_lead.pending_government_charges, 0)
                    else coalesce(v_lead.pending_professional_fees, 0) end;
  if p_amount > v_balance then
    raise exception 'Amount exceeds the pending % balance of %.', replace(p_component, '_', ' '), v_balance;
  end if;

  v_credited := coalesce(v_lead.owner_user_id, v_lead.created_by, v_uid);
  select coalesce(nullif(v_lead.owner, ''), u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1), '')
    into v_credited_name from auth.users u where u.id = v_credited;
  select coalesce(u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1), '')
    into v_recorder_name from auth.users u where u.id = v_uid;
  if p_component = 'professional_fees' then
    select coalesce(r.commission_rate, 0) into v_rate from public.user_roles r where r.user_id = v_credited;
    v_rate := coalesce(v_rate, 0);
  end if;

  insert into public.payment_collections (
    lead_id, amount, collected_on, created_by, created_by_name,
    credited_user_id, credited_user_name, commission_rate, commission_amount,
    government_charges_amount, professional_fees_amount, payment_component)
  values (
    p_lead_id, p_amount, v_on, v_uid, coalesce(v_recorder_name, ''),
    v_credited, coalesce(v_credited_name, ''), v_rate, round(p_amount * v_rate / 100, 2),
    case when p_component = 'government_charges' then p_amount else 0 end,
    case when p_component = 'professional_fees' then p_amount else 0 end,
    p_component)
  returning * into v_row;

  v_gov := coalesce(v_lead.pending_government_charges, 0) - case when p_component = 'government_charges' then p_amount else 0 end;
  v_prof := coalesce(v_lead.pending_professional_fees, 0) - case when p_component = 'professional_fees' then p_amount else 0 end;
  v_pending := round(v_gov + v_prof, 2);

  update public.leads set
    pending_government_charges = round(v_gov, 2),
    pending_professional_fees = round(v_prof, 2),
    pending_payment = v_pending,
    payment_status = case when v_pending > 0 then 'pending' else 'collected' end,
    payment_collected_at = case when v_pending > 0 then null else v_on end,
    payment_followup_date = case when v_pending > 0 then v_today + 1 else null end,
    last_contact = v_today,
    updated_at = now()
  where id = p_lead_id;

  return jsonb_build_object(
    'collection', to_jsonb(v_row),
    'lead', (select to_jsonb(l) from public.leads l where l.id = p_lead_id));
end;
$$;
revoke all on function public.record_payment(text, text, numeric, date) from public, anon;
grant execute on function public.record_payment(text, text, numeric, date) to authenticated;

-- 8. Team list for the owner dropdown --------------------------------------------
create or replace function public.list_team_members()
returns table (user_id uuid, full_name text, role text)
language sql stable security definer set search_path to '' as $$
  select r.user_id,
         coalesce(u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1)) as full_name,
         r.role
  from public.user_roles r join auth.users u on u.id = r.user_id
  where (select auth.uid()) is not null
  order by 2;
$$;
revoke all on function public.list_team_members() from public, anon;
grant execute on function public.list_team_members() to authenticated;

revoke all on function private.is_admin() from public, anon;
revoke all on function private.can_access_lead(text) from public, anon;
revoke all on function private.has_permission(text) from public, anon;
grant usage on schema private to authenticated;
grant execute on function private.is_admin() to authenticated;
grant execute on function private.can_access_lead(text) to authenticated;
grant execute on function private.has_permission(text) to authenticated;

commit;
