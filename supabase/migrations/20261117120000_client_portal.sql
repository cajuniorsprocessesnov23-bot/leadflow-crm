-- Client portal (legalwegal.com/Login): clients sign in with a WhatsApp OTP and see only
-- their own services. Uses the same Supabase project and auth as the CRM.
--
-- What this adds:
--   1. private.client_phone10(): last 10 digits of the signed-in user's phone (from the OTP login).
--      private.client_owns_lead(lead_id): true when that lead's phone matches.
--      private.is_staff(): true for anyone with a CRM role (staff/admin/super_admin).
--   2. Table client_documents: files a client uploads for a service. Staff who can open the lead
--      see and review them (accept/reject with a note); the client sees their own.
--   3. Private storage bucket "client-docs" (10 MB, PDF/images). Path: <phone10>/<lead_id>/<file>.
--      A client can upload/read only under their own phone folder and only for their own leads.
--      Staff read files of leads they can access (same rule as the CRM: owner/executor/creator/admin).
--   4. RPCs for the portal (all SECURITY DEFINER, all scoped to the caller's phone):
--        client_dashboard()            -> services, stage, fee/paid/balance, payments, documents
--                                         needed + uploaded, courier tracking, renewals, UPI ID.
--        client_add_document(...)      -> registers an uploaded file against a lead.
--        client_request_service(...)   -> creates a new CRM lead (source "Client portal") routed
--                                         to the service owner like other leads.
--      staff_review_document(...) for the CRM.
--
-- Impact on existing data: none. No existing table, policy or row changes. Clients have no
-- user_roles row, so every existing CRM policy already denies them; they only reach data via the
-- RPCs above. Staff CRM logins are unchanged.

create or replace function private.client_phone10() returns text
language sql stable security definer set search_path = '' as $$
  select nullif(right(regexp_replace(coalesce((select auth.jwt() ->> 'phone'), ''), '\D', '', 'g'), 10), '')
$$;

create or replace function private.is_staff() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.user_roles where user_id = (select auth.uid()))
$$;

create or replace function private.client_owns_lead(p_lead_id text) returns boolean
language sql stable security definer set search_path = '' as $$
  select private.client_phone10() is not null and exists (
    select 1 from public.leads l
     where l.id = p_lead_id
       and right(regexp_replace(coalesce(l.phone, ''), '\D', '', 'g'), 10) = private.client_phone10())
$$;

-- 2. Uploaded documents ---------------------------------------------------------------------
create table if not exists public.client_documents (
  id uuid primary key default gen_random_uuid(),
  lead_id text not null references public.leads(id) on delete cascade,
  doc_name text not null,
  storage_path text not null unique,
  file_name text,
  size_bytes integer,
  mime text,
  status text not null default 'uploaded' check (status in ('uploaded', 'accepted', 'rejected')),
  review_note text,
  uploaded_by uuid default auth.uid(),
  uploaded_at timestamptz not null default now(),
  reviewed_by uuid,
  reviewed_at timestamptz
);
create index if not exists client_documents_lead_idx on public.client_documents (lead_id);
alter table public.client_documents enable row level security;

drop policy if exists client_documents_staff_select on public.client_documents;
create policy client_documents_staff_select on public.client_documents for select to authenticated
  using (private.can_access_lead(lead_id));
drop policy if exists client_documents_client_select on public.client_documents;
create policy client_documents_client_select on public.client_documents for select to authenticated
  using (private.client_owns_lead(lead_id));

-- 3. Storage bucket -----------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('client-docs', 'client-docs', false, 10485760,
        array['application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'])
on conflict (id) do nothing;

drop policy if exists client_docs_client_insert on storage.objects;
create policy client_docs_client_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'client-docs'
    and (storage.foldername(name))[1] = private.client_phone10()
    and private.client_owns_lead((storage.foldername(name))[2]));
drop policy if exists client_docs_client_select on storage.objects;
create policy client_docs_client_select on storage.objects for select to authenticated
  using (bucket_id = 'client-docs'
    and (storage.foldername(name))[1] = private.client_phone10()
    and private.client_owns_lead((storage.foldername(name))[2]));
drop policy if exists client_docs_staff_select on storage.objects;
create policy client_docs_staff_select on storage.objects for select to authenticated
  using (bucket_id = 'client-docs' and private.is_staff()
    and private.can_access_lead((storage.foldername(name))[2]));

-- 4. Portal RPCs --------------------------------------------------------------------------------
create or replace function public.client_dashboard() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare v_phone text := private.client_phone10(); v jsonb;
begin
  if v_phone is null then raise exception 'Not signed in with a phone number'; end if;
  select jsonb_build_object(
    'phone', v_phone,
    'name', (select l.name from public.leads l
              where right(regexp_replace(coalesce(l.phone,''),'\D','','g'),10) = v_phone
              order by l.created_at desc limit 1),
    'upi_id', (select value from private.app_settings where key = 'upi_id'),
    'services', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', l.id, 'code', l.lead_code, 'services', l.lead_types, 'stage', l.stage,
        'status', case
            when l.stage = 'Work done' then 'Completed'
            when l.stage = 'Work processed' then 'In progress'
            when l.stage in ('Verified', 'Group made') then 'Documents & onboarding'
            else 'Enquiry received' end,
        'step', case
            when l.stage = 'Work done' then 4
            when l.stage = 'Work processed' then 3
            when l.stage in ('Verified', 'Group made') then 2
            else 1 end,
        'created_at', l.created_at, 'completed_date', l.completed_date, 'due_date', l.work_due_date,
        'fee', l.quoted_fee,
        'paid', coalesce((select sum(p.amount) from public.payment_collections p where p.lead_id = l.id), 0),
        'balance', coalesce(l.pending_payment, 0),
        'payments', coalesce((select jsonb_agg(jsonb_build_object('id', p.id, 'amount', p.amount,
                        'date', p.collected_on, 'type', p.payment_component) order by p.collected_on)
                        from public.payment_collections p where p.lead_id = l.id), '[]'::jsonb),
        'courier', case when l.tracking_id is not null then jsonb_build_object(
                        'name', l.courier_name, 'id', l.tracking_id, 'link', l.tracking_link) end,
        'documents_needed', coalesce((select jsonb_agg(jsonb_build_object('service', o.name, 'list', o.documents))
                        from public.lead_type_options o
                        where o.name = any(l.lead_types) and o.documents <> ''), '[]'::jsonb),
        'uploads', coalesce((select jsonb_agg(jsonb_build_object('id', d.id, 'doc_name', d.doc_name,
                        'file_name', d.file_name, 'path', d.storage_path, 'status', d.status,
                        'note', d.review_note, 'at', d.uploaded_at) order by d.uploaded_at desc)
                        from public.client_documents d where d.lead_id = l.id), '[]'::jsonb)
      ) order by l.created_at desc)
      from public.leads l
      where right(regexp_replace(coalesce(l.phone,''),'\D','','g'),10) = v_phone
        and l.stage not in ('False lead', 'Clear no lead', 'Work dropped')), '[]'::jsonb),
    'renewals', coalesce((
      select jsonb_agg(jsonb_build_object('service', r.service, 'due_date', r.due_date, 'status', r.status)
                       order by r.due_date)
      from public.client_renewals r join public.leads l on l.id = r.lead_id
      where right(regexp_replace(coalesce(l.phone,''),'\D','','g'),10) = v_phone
        and r.status = 'open'), '[]'::jsonb),
    'service_options', coalesce((select jsonb_agg(o.name order by o.sort_order)
                                 from public.lead_type_options o where o.active), '[]'::jsonb)
  ) into v;
  return v;
end $$;

create or replace function public.client_add_document(p_lead_id text, p_doc_name text, p_path text,
  p_file_name text, p_size integer, p_mime text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_id uuid;
begin
  if not private.client_owns_lead(p_lead_id) then raise exception 'Not your service'; end if;
  if split_part(p_path, '/', 1) <> private.client_phone10() or split_part(p_path, '/', 2) <> p_lead_id then
    raise exception 'Bad file path';
  end if;
  insert into public.client_documents (lead_id, doc_name, storage_path, file_name, size_bytes, mime)
  values (p_lead_id, left(coalesce(nullif(trim(p_doc_name), ''), 'Document'), 120), p_path,
          left(p_file_name, 200), p_size, left(p_mime, 80))
  returning id into v_id;
  return v_id;
end $$;

create or replace function public.client_request_service(p_services text[], p_note text default null)
returns text
language plpgsql security definer set search_path = '' as $$
declare v_phone text := private.client_phone10(); v_name text; v_owner uuid; v_owner_name text;
        v_id text := gen_random_uuid()::text; v_code text;
begin
  if v_phone is null then raise exception 'Not signed in'; end if;
  if coalesce(array_length(p_services, 1), 0) = 0 then raise exception 'Choose a service'; end if;
  select l.name into v_name from public.leads l
   where right(regexp_replace(coalesce(l.phone,''),'\D','','g'),10) = v_phone
   order by l.created_at desc limit 1;
  v_owner := public.lead_owner_for_services(p_services);
  if v_owner is null then
    select user_id into v_owner from public.user_roles order by (role = 'staff') desc limit 1;
  end if;
  select coalesce(u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1)) into v_owner_name
    from auth.users u where u.id = v_owner;
  select public.next_lead_code() into v_code;
  insert into public.leads (id, created_by, created_by_name, owner_user_id, name, phone, stage, arrival,
                            source, lead_code, lead_types, whatsapp_opt_in, notes)
  values (v_id, v_owner, v_owner_name, v_owner, coalesce(v_name, 'Client ' || v_phone), v_phone, 'Unverified',
          (now() at time zone 'Asia/Kolkata')::date, 'Client portal', v_code, p_services, true,
          left('Requested from client portal. ' || coalesce(p_note, ''), 5000));
  return v_id;
end $$;

create or replace function public.staff_review_document(p_id uuid, p_status text, p_note text default null)
returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p_status not in ('accepted', 'rejected', 'uploaded') then raise exception 'Bad status'; end if;
  update public.client_documents d set status = p_status, review_note = left(p_note, 500),
         reviewed_by = (select auth.uid()), reviewed_at = now()
   where d.id = p_id and private.can_access_lead(d.lead_id);
  if not found then raise exception 'Not allowed'; end if;
end $$;

revoke all on function public.client_dashboard() from public, anon;
revoke all on function public.client_add_document(text, text, text, text, integer, text) from public, anon;
revoke all on function public.client_request_service(text[], text) from public, anon;
revoke all on function public.staff_review_document(uuid, text, text) from public, anon;
grant execute on function public.client_dashboard() to authenticated;
grant execute on function public.client_add_document(text, text, text, text, integer, text) to authenticated;
grant execute on function public.client_request_service(text[], text) to authenticated;
grant execute on function public.staff_review_document(uuid, text, text) to authenticated;
