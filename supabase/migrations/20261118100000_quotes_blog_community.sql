-- Quotes, blog and community Q&A (18 Nov 2026). Approved by Kunal 18 Nov:
--   quote layout "Approve as is", sending "WhatsApp link + PDF", payment "50% advance, 50% before filing",
--   blog + Q&A "Yes, apply".
-- Impact on existing data: none. Only new tables, functions and one storage bucket are added.
--
-- 1. QUOTES
--    Staff create a draft for a lead and submit it. Nothing reaches the client until the Super Admin
--    approves it (approve_quote). Approval queues WhatsApp template lw_c_quote (header = the PDF,
--    button = the quote page). The template must be approved by Meta first; until then the message
--    waits in the queue (the dispatcher already holds messages whose template isn't approved).
--    The client opens www.legalwegal.com/quote/?t=<token>; quote_public(token) returns only that quote.
-- 2. BLOG: posts written in the CRM by Admins; the public reads published posts only.
-- 3. COMMUNITY Q&A: logged-in visitors (WhatsApp OTP) ask and answer; everything waits for Admin
--    moderation, except answers by staff, which publish directly. Phone numbers are never public.

begin;

-- 1. Quotes -------------------------------------------------------------------------------------
create sequence if not exists public.quote_no_seq;
create table if not exists public.quotes (
  id uuid primary key default gen_random_uuid(),
  quote_no text unique not null default ('LW-Q-' || lpad(nextval('public.quote_no_seq')::text, 4, '0')),
  lead_id text not null references public.leads(id) on delete cascade,
  client_name text not null default '',
  client_phone text not null default '',
  client_place text not null default '',
  service text not null,
  service_details text not null default '',
  items jsonb not null default '[]'::jsonb,          -- [{section:'fee'|'govt', desc, amount}]
  gst_rate numeric not null default 18,
  fee_total numeric not null default 0,
  gst_amount numeric not null default 0,
  govt_total numeric not null default 0,
  total numeric not null default 0,
  advance_pct numeric not null default 50,
  timeline text[] not null default '{}',
  documents text[] not null default '{}',
  notes text not null default '',
  valid_till date not null default ((now() at time zone 'Asia/Kolkata')::date + 14),
  status text not null default 'draft' check (status in ('draft', 'pending_approval', 'approved', 'sent', 'accepted', 'rejected', 'cancelled')),
  public_token uuid not null default gen_random_uuid() unique,
  pdf_url text not null default '',
  expert_name text not null default '',
  created_by uuid default auth.uid() references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  submitted_at timestamptz,
  approved_by uuid references auth.users(id) on delete set null,
  approved_at timestamptz,
  sent_at timestamptz,
  viewed_at timestamptz,
  review_note text not null default ''
);
create index if not exists quotes_lead_idx on public.quotes (lead_id, created_at desc);
create index if not exists quotes_status_idx on public.quotes (status);
alter table public.quotes enable row level security;

drop policy if exists quotes_staff_read on public.quotes;
create policy quotes_staff_read on public.quotes for select to authenticated
  using (private.is_admin() or private.can_access_lead(lead_id));
drop policy if exists quotes_staff_insert on public.quotes;
create policy quotes_staff_insert on public.quotes for insert to authenticated
  with check (private.can_access_lead(lead_id) and status in ('draft', 'pending_approval'));
drop policy if exists quotes_staff_update on public.quotes;
create policy quotes_staff_update on public.quotes for update to authenticated
  using ((private.is_admin() or private.can_access_lead(lead_id)) and status in ('draft', 'pending_approval', 'rejected'))
  with check (status in ('draft', 'pending_approval', 'cancelled') or private.is_super_admin());
drop policy if exists quotes_super_admin_all on public.quotes;
create policy quotes_super_admin_all on public.quotes for all to authenticated
  using (private.is_super_admin()) with check (private.is_super_admin());

-- Totals are always recomputed from items, so a quote can't show a wrong total.
create or replace function private.quote_totals() returns trigger
language plpgsql set search_path = '' as $$
begin
  select coalesce(sum((i ->> 'amount')::numeric) filter (where i ->> 'section' = 'fee'), 0),
         coalesce(sum((i ->> 'amount')::numeric) filter (where i ->> 'section' = 'govt'), 0)
    into new.fee_total, new.govt_total
    from jsonb_array_elements(coalesce(new.items, '[]'::jsonb)) i;
  new.gst_amount := round(new.fee_total * coalesce(new.gst_rate, 0) / 100, 2);
  new.total := new.fee_total + new.gst_amount + new.govt_total;
  new.updated_at := now();
  if new.status = 'pending_approval' and (tg_op = 'INSERT' or old.status <> 'pending_approval') then new.submitted_at := now(); end if;
  return new;
end $$;
drop trigger if exists quote_totals on public.quotes;
create trigger quote_totals before insert or update on public.quotes
  for each row execute function private.quote_totals();

-- Super Admin approves (and the WhatsApp is queued) or sends it back with a note.
create or replace function public.approve_quote(p_id uuid, p_pdf_url text default '') returns jsonb
language plpgsql security definer set search_path = '' as $$
declare q public.quotes; l public.leads;
begin
  if not private.is_super_admin() then raise exception 'Only the Super Admin can approve quotes'; end if;
  select * into q from public.quotes where id = p_id for update;
  if not found then raise exception 'Quote not found'; end if;
  if q.status not in ('draft', 'pending_approval') then raise exception 'Quote is already %', q.status; end if;
  select * into l from public.leads where id = q.lead_id;
  update public.quotes set status = 'sent', approved_by = auth.uid(), approved_at = now(), sent_at = now(),
         pdf_url = coalesce(nullif(p_pdf_url, ''), pdf_url) where id = p_id returning * into q;
  if l.whatsapp_opt_in then
    perform private.wa_enqueue(l.id, coalesce(nullif(q.client_phone, ''), l.phone), 'client', null, 'C-quote', 'lw_c_quote',
      jsonb_build_object(
        'body', jsonb_build_array(coalesce(nullif(trim(q.client_name), ''), 'there'), q.quote_no, q.service,
                  to_char(q.total, 'FM99,99,99,990'), to_char(q.valid_till, 'DD Mon YYYY')),
        'header_document', case when q.pdf_url <> '' then jsonb_build_object('link', q.pdf_url, 'filename', q.quote_no || '.pdf') end,
        'button_url', q.public_token::text),
      'CQ:' || q.id);
  end if;
  return jsonb_build_object('ok', true, 'quote_no', q.quote_no, 'whatsapp', l.whatsapp_opt_in);
end $$;

create or replace function public.return_quote(p_id uuid, p_note text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not private.is_super_admin() then raise exception 'Only the Super Admin can review quotes'; end if;
  update public.quotes set status = 'rejected', review_note = left(coalesce(p_note, ''), 1000)
   where id = p_id and status in ('draft', 'pending_approval');
end $$;

-- Public view of one quote by its secret token (no login). Only approved/sent/accepted quotes.
create or replace function public.quote_public(p_token uuid) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare q public.quotes; l public.leads;
begin
  select * into q from public.quotes where public_token = p_token and status in ('approved', 'sent', 'accepted');
  if not found then return null; end if;
  select * into l from public.leads where id = q.lead_id;
  if q.viewed_at is null then update public.quotes set viewed_at = now() where id = q.id; end if;
  return jsonb_build_object('quote_no', q.quote_no, 'date', q.approved_at, 'valid_till', q.valid_till,
    'client_name', q.client_name, 'client_phone_masked', '+91 ' || left(right(q.client_phone, 10), 2) || 'XXX XX' || right(q.client_phone, 3),
    'client_place', q.client_place, 'lead_code', l.lead_code, 'service', q.service, 'service_details', q.service_details,
    'items', q.items, 'gst_rate', q.gst_rate, 'fee_total', q.fee_total, 'gst_amount', q.gst_amount, 'govt_total', q.govt_total,
    'total', q.total, 'advance_pct', q.advance_pct, 'timeline', q.timeline, 'documents', q.documents, 'notes', q.notes,
    'expert_name', q.expert_name, 'status', q.status, 'pdf_url', q.pdf_url,
    'expired', q.valid_till < (now() at time zone 'Asia/Kolkata')::date);
end $$;

create or replace function public.accept_quote(p_token uuid) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  update public.quotes set status = 'accepted' where public_token = p_token and status = 'sent'
     and valid_till >= (now() at time zone 'Asia/Kolkata')::date;
  return found;
end $$;

revoke all on function public.approve_quote(uuid, text), public.return_quote(uuid, text) from public, anon;
grant execute on function public.approve_quote(uuid, text), public.return_quote(uuid, text) to authenticated;
revoke all on function public.quote_public(uuid), public.accept_quote(uuid) from public;
grant execute on function public.quote_public(uuid), public.accept_quote(uuid) to anon, authenticated;

-- PDFs: public-read bucket (file names contain the random token, so they can't be guessed).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('quotes', 'quotes', true, 5242880, array['application/pdf'])
on conflict (id) do nothing;
drop policy if exists quotes_pdf_staff_write on storage.objects;
create policy quotes_pdf_staff_write on storage.objects for insert to authenticated
  with check (bucket_id = 'quotes' and private.is_staff());
drop policy if exists quotes_pdf_staff_update on storage.objects;
create policy quotes_pdf_staff_update on storage.objects for update to authenticated
  using (bucket_id = 'quotes' and private.is_staff());

-- 2. Blog ---------------------------------------------------------------------------------------
create table if not exists public.blog_posts (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  title text not null,
  excerpt text not null default '',
  body_html text not null default '',
  cover_url text not null default '',
  category text not null default '',
  tags text[] not null default '{}',
  service_slug text not null default '',
  seo_title text not null default '',
  seo_description text not null default '',
  author_name text not null default 'Legal Wegal Team',
  status text not null default 'draft' check (status in ('draft', 'published', 'archived')),
  published_at timestamptz,
  created_by uuid default auth.uid() references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.blog_posts enable row level security;
drop policy if exists blog_public_read on public.blog_posts;
create policy blog_public_read on public.blog_posts for select to anon, authenticated using (status = 'published');
drop policy if exists blog_admin_all on public.blog_posts;
create policy blog_admin_all on public.blog_posts for all to authenticated using (private.is_admin()) with check (private.is_admin());

-- 3. Community Q&A ------------------------------------------------------------------------------
create table if not exists public.community_questions (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  title text not null,
  body text not null default '',
  category text not null default 'General',
  asker_name text not null default 'Anonymous',
  user_id uuid references auth.users(id) on delete set null,
  asker_phone10 text not null default '',
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  answer_count integer not null default 0,
  created_at timestamptz not null default now()
);
create table if not exists public.community_answers (
  id uuid primary key default gen_random_uuid(),
  question_id uuid not null references public.community_questions(id) on delete cascade,
  body text not null,
  answerer_name text not null default 'Anonymous',
  user_id uuid references auth.users(id) on delete set null,
  is_staff_answer boolean not null default false,
  is_accepted boolean not null default false,
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  upvotes integer not null default 0,
  created_at timestamptz not null default now()
);
create table if not exists public.community_votes (
  answer_id uuid not null references public.community_answers(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (answer_id, user_id)
);
create index if not exists cq_status_idx on public.community_questions (status, created_at desc);
create index if not exists ca_q_idx on public.community_answers (question_id, status);
alter table public.community_questions enable row level security;
alter table public.community_answers enable row level security;
alter table public.community_votes enable row level security;

-- The public sees approved content only, and never the phone column.
drop policy if exists cq_public_read on public.community_questions;
create policy cq_public_read on public.community_questions for select to anon using (status = 'approved');
drop policy if exists cq_user_read on public.community_questions;
create policy cq_user_read on public.community_questions for select to authenticated using (status = 'approved' or user_id = (select auth.uid()) or private.is_staff());
drop policy if exists cq_admin_all on public.community_questions;
create policy cq_admin_all on public.community_questions for all to authenticated using (private.is_admin()) with check (private.is_admin());
drop policy if exists ca_public_read on public.community_answers;
create policy ca_public_read on public.community_answers for select to anon using (status = 'approved');
drop policy if exists ca_user_read on public.community_answers;
create policy ca_user_read on public.community_answers for select to authenticated using (status = 'approved' or user_id = (select auth.uid()) or private.is_staff());
drop policy if exists ca_admin_all on public.community_answers;
create policy ca_admin_all on public.community_answers for all to authenticated using (private.is_admin()) with check (private.is_admin());
revoke select on public.community_questions from anon, authenticated;
grant select (id, slug, title, body, category, asker_name, status, answer_count, created_at) on public.community_questions to anon, authenticated;
grant select on public.community_questions to service_role;
revoke insert, update, delete on public.community_questions, public.community_answers, public.community_votes from anon;

create or replace function public.community_ask(p_title text, p_body text, p_category text, p_name text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_id uuid; v_slug text; v_n int;
begin
  if auth.uid() is null then raise exception 'Log in with your mobile number to ask'; end if;
  if length(trim(coalesce(p_title, ''))) < 10 then raise exception 'Please write your question in at least 10 characters'; end if;
  select count(*) into v_n from public.community_questions where user_id = auth.uid() and created_at > now() - interval '1 day';
  if v_n >= 5 then raise exception 'You can ask up to 5 questions a day'; end if;
  v_slug := trim(both '-' from left(regexp_replace(lower(trim(p_title)), '[^a-z0-9]+', '-', 'g'), 70)) || '-' || substr(md5(random()::text), 1, 5);
  insert into public.community_questions (slug, title, body, category, asker_name, user_id, asker_phone10)
  values (v_slug, left(trim(p_title), 200), left(coalesce(p_body, ''), 4000), left(coalesce(nullif(p_category, ''), 'General'), 60),
          left(coalesce(nullif(trim(p_name), ''), 'Anonymous'), 60), auth.uid(), coalesce(private.client_phone10(), ''))
  returning id into v_id;
  return v_id;
end $$;

create or replace function public.community_answer(p_question uuid, p_body text, p_name text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v_id uuid; v_staff boolean := private.is_staff(); v_n int;
begin
  if auth.uid() is null then raise exception 'Log in with your mobile number to answer'; end if;
  if length(trim(coalesce(p_body, ''))) < 20 then raise exception 'Please write at least 20 characters'; end if;
  if not exists (select 1 from public.community_questions where id = p_question and status = 'approved') then raise exception 'Question not found'; end if;
  select count(*) into v_n from public.community_answers where user_id = auth.uid() and created_at > now() - interval '1 day';
  if not v_staff and v_n >= 10 then raise exception 'You can post up to 10 answers a day'; end if;
  insert into public.community_answers (question_id, body, answerer_name, user_id, is_staff_answer, status)
  values (p_question, left(trim(p_body), 6000),
          case when v_staff then 'Legal Wegal Expert' else left(coalesce(nullif(trim(p_name), ''), 'Anonymous'), 60) end,
          auth.uid(), v_staff, case when v_staff then 'approved' else 'pending' end)
  returning id into v_id;
  return v_id;
end $$;

create or replace function public.community_vote(p_answer uuid) returns integer
language plpgsql security definer set search_path = '' as $$
declare v int;
begin
  if auth.uid() is null then raise exception 'Log in to vote'; end if;
  insert into public.community_votes (answer_id, user_id) values (p_answer, auth.uid()) on conflict do nothing;
  update public.community_answers set upvotes = (select count(*) from public.community_votes where answer_id = p_answer)
   where id = p_answer returning upvotes into v;
  return v;
end $$;

-- Keeps answer_count right whenever an answer's status changes.
create or replace function private.community_count() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  update public.community_questions q set answer_count = (select count(*) from public.community_answers a where a.question_id = q.id and a.status = 'approved')
   where q.id = coalesce(new.question_id, old.question_id);
  return null;
end $$;
drop trigger if exists community_count on public.community_answers;
create trigger community_count after insert or update or delete on public.community_answers
  for each row execute function private.community_count();

revoke all on function public.community_ask(text, text, text, text), public.community_answer(uuid, text, text), public.community_vote(uuid) from public, anon;
grant execute on function public.community_ask(text, text, text, text), public.community_answer(uuid, text, text), public.community_vote(uuid) to authenticated;

commit;
