-- B2B partners, automatic commissions and customer referrals (decided by Kunal, 17 Nov 2026).
--
-- Decisions:
--   * Two partner models, chosen per partner by an Admin: 'referral' (earns commission) and
--     'reseller' (buys at a wholesale price, bills the client; no commission).
--   * Commission is on OUR professional fee only, never on government fees.
--   * Commission is payable right after the client's payment is recorded (status 'approved').
--   * TDS (s.194H / s.393(1)): 2% once the partner's commission in the financial year crosses
--     Rs 20,000; 20% if no PAN. Both values are settings, not code.
--   * Customer referral reward = cash to the referrer's UPI, set in Settings (referral_reward_amount).
--
-- Adds:
--   partners                    one row per partner firm (signs up with WhatsApp OTP; Admin approves)
--   partner_commission_rules    % or flat Rs per service; partner-specific rule beats the default
--   partner_wholesale_prices    reseller prices per service (optional per partner)
--   partner_commissions         ledger: approved -> paid (or reversed if the payment is deleted)
--   referrals                   client-to-client referrals and their cash rewards
--   leads.partner_id, leads.referral_code_used
--   settings: tds_rate, tds_rate_no_pan, tds_threshold, referral_reward_amount, min_payout
--   triggers on payment_collections (insert -> commission / referral reward; delete -> reversal)
--   RPCs for the partner portal and the client portal (all scoped to the caller's WhatsApp login)
--
-- Impact on existing data: none. Existing leads get partner_id = null. Existing payments are not
-- back-filled with commissions. Staff permissions are unchanged; only Admin / Super Admin can see
-- or change partners, rules and payouts.

-- 1. Partners ------------------------------------------------------------------------------------
create table if not exists public.partners (
  id uuid primary key default gen_random_uuid(),
  code text unique,
  firm_name text not null,
  contact_name text not null,
  phone text not null,
  email text,
  city text,
  pan text,
  gstin text,
  upi_id text,
  bank_details text,
  model text not null default 'referral' check (model in ('referral', 'reseller')),
  tier text not null default 'standard',
  status text not null default 'pending' check (status in ('pending', 'active', 'paused', 'rejected')),
  manager_user_id uuid references auth.users(id) on delete set null,
  notes text,
  terms_accepted_at timestamptz,
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  approved_by uuid references auth.users(id) on delete set null
);
create unique index if not exists partners_phone10_idx on public.partners (right(regexp_replace(phone, '\D', '', 'g'), 10));
alter table public.partners enable row level security;
drop policy if exists partners_admin_all on public.partners;
create policy partners_admin_all on public.partners for all to authenticated
  using (private.is_admin()) with check (private.is_admin());
drop policy if exists partners_manager_read on public.partners;
create policy partners_manager_read on public.partners for select to authenticated
  using (manager_user_id = (select auth.uid()));

create or replace function private.partner_id_for_caller() returns uuid
language sql stable security definer set search_path = '' as $$
  select p.id from public.partners p
   where private.client_phone10() is not null
     and right(regexp_replace(p.phone, '\D', '', 'g'), 10) = private.client_phone10()
   limit 1
$$;

-- 2. Rules and prices ----------------------------------------------------------------------------
create table if not exists public.partner_commission_rules (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid references public.partners(id) on delete cascade,  -- null = default for everyone
  service text not null default '*',                                  -- lead type name, or * = any
  kind text not null default 'percent' check (kind in ('percent', 'flat')),
  value numeric(12,2) not null check (value >= 0),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (partner_id, service)
);
alter table public.partner_commission_rules enable row level security;
drop policy if exists pcr_admin_all on public.partner_commission_rules;
create policy pcr_admin_all on public.partner_commission_rules for all to authenticated
  using (private.is_admin()) with check (private.is_admin());

create table if not exists public.partner_wholesale_prices (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid references public.partners(id) on delete cascade,  -- null = default wholesale list
  service text not null,
  price numeric(12,2) not null check (price >= 0),
  unique (partner_id, service)
);
alter table public.partner_wholesale_prices enable row level security;
drop policy if exists pwp_admin_all on public.partner_wholesale_prices;
create policy pwp_admin_all on public.partner_wholesale_prices for all to authenticated
  using (private.is_admin()) with check (private.is_admin());

-- 3. Lead links ----------------------------------------------------------------------------------
alter table public.leads add column if not exists partner_id uuid references public.partners(id) on delete set null;
alter table public.leads add column if not exists referral_code_used text;
create index if not exists leads_partner_idx on public.leads (partner_id) where partner_id is not null;

-- 4. Commission ledger ---------------------------------------------------------------------------
create table if not exists public.partner_commissions (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.partners(id) on delete restrict,
  lead_id text not null references public.leads(id) on delete cascade,
  payment_id uuid unique references public.payment_collections(id) on delete set null,
  service text,
  base_amount numeric(12,2) not null,
  rule_kind text not null,
  rule_value numeric(12,2) not null,
  gross numeric(12,2) not null,
  tds numeric(12,2) not null default 0,
  net numeric(12,2) not null,
  status text not null default 'approved' check (status in ('approved', 'paid', 'reversed')),
  payout_ref text,
  paid_at timestamptz,
  paid_by uuid references auth.users(id) on delete set null,
  note text,
  created_at timestamptz not null default now()
);
create index if not exists partner_commissions_partner_idx on public.partner_commissions (partner_id, status);
alter table public.partner_commissions enable row level security;
drop policy if exists pc_admin_all on public.partner_commissions;
create policy pc_admin_all on public.partner_commissions for all to authenticated
  using (private.is_admin()) with check (private.is_admin());

-- 5. Customer referrals --------------------------------------------------------------------------
create table if not exists public.referrals (
  id uuid primary key default gen_random_uuid(),
  code text not null,                      -- the referrer's code (LWR-<last 6 digits>)
  referrer_phone10 text not null,
  referred_lead_id text not null unique references public.leads(id) on delete cascade,
  status text not null default 'joined' check (status in ('joined', 'payable', 'paid', 'cancelled')),
  reward_amount numeric(12,2),
  referrer_upi text,
  payout_ref text,
  paid_at timestamptz,
  created_at timestamptz not null default now()
);
alter table public.referrals enable row level security;
drop policy if exists referrals_admin_all on public.referrals;
create policy referrals_admin_all on public.referrals for all to authenticated
  using (private.is_admin()) with check (private.is_admin());

-- 6. Settings ------------------------------------------------------------------------------------
insert into private.app_settings (key, value) values
  ('tds_rate', '2'), ('tds_rate_no_pan', '20'), ('tds_threshold', '20000'),
  ('referral_reward_amount', '0'), ('min_payout', '500')
on conflict (key) do nothing;

create or replace function private.setting_num(p_key text, p_default numeric) returns numeric
language sql stable security definer set search_path = '' as $$
  select coalesce((select nullif(value, '')::numeric from private.app_settings where key = p_key), p_default)
$$;

-- 7. Commission + referral reward on payment -----------------------------------------------------
create or replace function private.on_payment_partner_and_referral() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
  l public.leads; p public.partners; r public.partner_commission_rules;
  v_base numeric; v_gross numeric; v_tds numeric := 0; v_fy_start date; v_fy_total numeric;
  v_service text; v_reward numeric;
begin
  select * into l from public.leads where id = new.lead_id;
  if not found then return new; end if;

  -- Partner commission (referral partners only, our professional fee only)
  if l.partner_id is not null then
    select * into p from public.partners where id = l.partner_id;
    v_base := coalesce(nullif(new.professional_fees_amount, 0),
                       case when new.payment_component = 'professional_fees' then new.amount else 0 end);
    if p.status = 'active' and p.model = 'referral' and v_base > 0 then
      v_service := coalesce(l.lead_types[1], '*');
      select * into r from public.partner_commission_rules x
       where x.active and (x.partner_id = p.id or x.partner_id is null)
         and (x.service = any(coalesce(l.lead_types, '{}')) or x.service = '*')
       order by (x.partner_id is not null) desc, (x.service <> '*') desc, x.value desc
       limit 1;
      if found then
        v_gross := round(case when r.kind = 'percent' then v_base * r.value / 100 else r.value end, 2);
        if v_gross > 0 then
          v_fy_start := make_date(extract(year from (now() at time zone 'Asia/Kolkata' - interval '3 months'))::int, 4, 1);
          select coalesce(sum(gross), 0) into v_fy_total from public.partner_commissions
           where partner_id = p.id and status <> 'reversed' and created_at >= v_fy_start;
          if coalesce(p.pan, '') = '' then
            v_tds := round(v_gross * private.setting_num('tds_rate_no_pan', 20) / 100, 2);
          elsif v_fy_total + v_gross > private.setting_num('tds_threshold', 20000) then
            v_tds := round(v_gross * private.setting_num('tds_rate', 2) / 100, 2);
          end if;
          insert into public.partner_commissions (partner_id, lead_id, payment_id, service, base_amount,
                                                  rule_kind, rule_value, gross, tds, net, status)
          values (p.id, l.id, new.id, v_service, v_base, r.kind, r.value, v_gross, v_tds, v_gross - v_tds, 'approved')
          on conflict (payment_id) do nothing;
        end if;
      end if;
    end if;
  end if;

  -- Customer referral: first payment by the referred client makes the reward payable
  v_reward := private.setting_num('referral_reward_amount', 0);
  update public.referrals set status = 'payable', reward_amount = v_reward
   where referred_lead_id = l.id and status = 'joined' and v_reward > 0;
  return new;
end $$;

drop trigger if exists payment_partner_and_referral on public.payment_collections;
create trigger payment_partner_and_referral after insert on public.payment_collections
  for each row execute function private.on_payment_partner_and_referral();

create or replace function private.on_payment_deleted_reverse() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  update public.partner_commissions set status = 'reversed', note = 'Payment deleted'
   where payment_id = old.id and status = 'approved';
  return old;
end $$;
drop trigger if exists payment_deleted_reverse on public.payment_collections;
create trigger payment_deleted_reverse before delete on public.payment_collections
  for each row execute function private.on_payment_deleted_reverse();

-- 8. Tagging new leads with a partner / referral code -------------------------------------------
-- Called by web-lead (service role) and by the portals.
create or replace function public.tag_lead_with_code(p_lead_id text, p_code text) returns text
language plpgsql security definer set search_path = '' as $$
declare v_code text := upper(trim(coalesce(p_code, ''))); v_pid uuid; v_ref text; l public.leads;
begin
  if v_code = '' then return 'none'; end if;
  select * into l from public.leads where id = p_lead_id;
  if not found then return 'no lead'; end if;
  select id into v_pid from public.partners where upper(code) = v_code and status = 'active';
  if v_pid is not null then
    update public.leads set partner_id = coalesce(partner_id, v_pid), referral_code_used = v_code where id = p_lead_id;
    return 'partner';
  end if;
  if v_code like 'LWR-%' then
    v_ref := substr(v_code, 5);
    if right(regexp_replace(coalesce(l.phone, ''), '\D', '', 'g'), 6) = v_ref then return 'self'; end if;
    -- referrer = most recent lead whose phone ends with those 6 digits and has paid at least once
    insert into public.referrals (code, referrer_phone10, referred_lead_id)
    select v_code, right(regexp_replace(x.phone, '\D', '', 'g'), 10), p_lead_id
      from public.leads x
     where right(regexp_replace(coalesce(x.phone, ''), '\D', '', 'g'), 6) = v_ref
       and exists (select 1 from public.payment_collections pc where pc.lead_id = x.id)
     order by x.created_at desc limit 1
    on conflict (referred_lead_id) do nothing;
    update public.leads set referral_code_used = v_code where id = p_lead_id;
    return 'referral';
  end if;
  return 'unknown';
end $$;
revoke all on function public.tag_lead_with_code(text, text) from public, anon, authenticated;
grant execute on function public.tag_lead_with_code(text, text) to service_role;

-- 9. Partner portal RPCs (caller = partner's WhatsApp login) ------------------------------------
create or replace function public.partner_signup(p_firm text, p_name text, p_email text, p_city text,
  p_pan text, p_gstin text, p_upi text, p_model text default 'referral') returns jsonb
language plpgsql security definer set search_path = '' as $$
declare v_phone text := private.client_phone10(); v_id uuid;
begin
  if v_phone is null then raise exception 'Log in with your mobile number first'; end if;
  if coalesce(trim(p_firm), '') = '' or coalesce(trim(p_name), '') = '' then raise exception 'Firm and name are required'; end if;
  select id into v_id from public.partners where right(regexp_replace(phone, '\D', '', 'g'), 10) = v_phone;
  if v_id is not null then return jsonb_build_object('id', v_id, 'existing', true); end if;
  insert into public.partners (firm_name, contact_name, phone, email, city, pan, gstin, upi_id, model, terms_accepted_at)
  values (left(trim(p_firm), 120), left(trim(p_name), 120), v_phone, left(p_email, 120), left(p_city, 80),
          upper(left(trim(coalesce(p_pan, '')), 10)), upper(left(trim(coalesce(p_gstin, '')), 15)), left(p_upi, 80),
          case when p_model = 'reseller' then 'reseller' else 'referral' end, now())
  returning id into v_id;
  return jsonb_build_object('id', v_id, 'existing', false);
end $$;

create or replace function public.partner_dashboard() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare v_pid uuid := private.partner_id_for_caller(); p public.partners;
begin
  if v_pid is null then return jsonb_build_object('registered', false); end if;
  select * into p from public.partners where id = v_pid;
  return jsonb_build_object(
    'registered', true,
    'partner', jsonb_build_object('firm', p.firm_name, 'name', p.contact_name, 'code', p.code, 'status', p.status,
                                  'model', p.model, 'tier', p.tier, 'upi', p.upi_id, 'pan_set', coalesce(p.pan, '') <> ''),
    'clients', coalesce((select jsonb_agg(jsonb_build_object(
        'id', l.id, 'code', l.lead_code, 'name', l.name, 'services', l.lead_types, 'created_at', l.created_at,
        'status', case when l.stage = 'Work done' then 'Completed' when l.stage = 'Work processed' then 'In progress'
                       when l.stage in ('Verified', 'Group made') then 'Documents & onboarding'
                       when l.stage in ('False lead', 'Clear no lead') then 'Closed'
                       when l.stage = 'Work dropped' then 'On hold' else 'Enquiry received' end,
        'paid', coalesce((select sum(pc.amount) from public.payment_collections pc where pc.lead_id = l.id), 0))
        order by l.created_at desc) from public.leads l where l.partner_id = v_pid), '[]'::jsonb),
    'commissions', coalesce((select jsonb_agg(jsonb_build_object('date', c.created_at, 'service', c.service,
        'base', c.base_amount, 'gross', c.gross, 'tds', c.tds, 'net', c.net, 'status', c.status, 'paid_at', c.paid_at,
        'ref', c.payout_ref) order by c.created_at desc) from public.partner_commissions c where c.partner_id = v_pid), '[]'::jsonb),
    'totals', (select jsonb_build_object(
        'earned', coalesce(sum(net) filter (where status <> 'reversed'), 0),
        'payable', coalesce(sum(net) filter (where status = 'approved'), 0),
        'paid', coalesce(sum(net) filter (where status = 'paid'), 0))
        from public.partner_commissions where partner_id = v_pid),
    'rules', coalesce((select jsonb_agg(jsonb_build_object('service', x.service, 'kind', x.kind, 'value', x.value))
        from public.partner_commission_rules x where x.active and (x.partner_id = v_pid or x.partner_id is null)), '[]'::jsonb),
    'wholesale', case when p.model = 'reseller' then coalesce((select jsonb_agg(jsonb_build_object('service', w.service, 'price', w.price))
        from public.partner_wholesale_prices w where w.partner_id = v_pid or w.partner_id is null), '[]'::jsonb) else '[]'::jsonb end,
    'service_options', coalesce((select jsonb_agg(o.name order by o.sort_order) from public.lead_type_options o where o.active), '[]'::jsonb)
  );
end $$;

create or replace function public.partner_add_client(p_name text, p_phone text, p_services text[], p_note text default null)
returns text
language plpgsql security definer set search_path = '' as $$
declare v_pid uuid := private.partner_id_for_caller(); p public.partners; v_ten text; v_owner uuid; v_owner_name text;
        v_id text := gen_random_uuid()::text; v_code text; v_existing text;
begin
  if v_pid is null then raise exception 'Not a registered partner'; end if;
  select * into p from public.partners where id = v_pid;
  if p.status <> 'active' then raise exception 'Your partner account is not active yet'; end if;
  v_ten := right(regexp_replace(coalesce(p_phone, ''), '\D', '', 'g'), 10);
  if v_ten !~ '^[6-9][0-9]{9}$' then raise exception 'Enter a valid 10-digit mobile number'; end if;
  if coalesce(trim(p_name), '') = '' then raise exception 'Enter the client name'; end if;
  select id into v_existing from public.leads where right(regexp_replace(coalesce(phone, ''), '\D', '', 'g'), 10) = v_ten
   order by created_at desc limit 1;
  if v_existing is not null then
    raise exception 'This client is already with Legal Wegal. Contact your relationship manager.';
  end if;
  v_owner := coalesce(p.manager_user_id, public.lead_owner_for_services(coalesce(p_services, '{}')));
  if v_owner is null then select user_id into v_owner from public.user_roles order by (role = 'staff') desc limit 1; end if;
  select coalesce(u.raw_user_meta_data ->> 'full_name', split_part(u.email, '@', 1)) into v_owner_name from auth.users u where u.id = v_owner;
  select public.next_lead_code() into v_code;
  insert into public.leads (id, created_by, created_by_name, owner_user_id, name, phone, stage, arrival, source,
                            lead_code, lead_types, whatsapp_opt_in, partner_id, referral_code_used, notes)
  values (v_id, v_owner, v_owner_name, v_owner, left(trim(p_name), 120), v_ten, 'Unverified',
          (now() at time zone 'Asia/Kolkata')::date, 'Partner', v_code, coalesce(p_services, '{}'), true, v_pid, p.code,
          left('Added by partner ' || p.firm_name || ' (' || coalesce(p.code, '') || '). ' || coalesce(p_note, ''), 5000));
  return v_id;
end $$;

-- 10. Client portal: referral code and cash rewards ---------------------------------------------
create or replace function public.client_referral_info() returns jsonb
language sql stable security definer set search_path = '' as $$
  select case when private.client_phone10() is null then null else jsonb_build_object(
    'code', 'LWR-' || right(private.client_phone10(), 6),
    'reward', private.setting_num('referral_reward_amount', 0),
    'referrals', coalesce((select jsonb_agg(jsonb_build_object('date', r.created_at, 'status', r.status,
                   'reward', r.reward_amount, 'paid_at', r.paid_at) order by r.created_at desc)
                 from public.referrals r where r.referrer_phone10 = private.client_phone10()), '[]'::jsonb),
    'upi', (select r.referrer_upi from public.referrals r where r.referrer_phone10 = private.client_phone10()
             and r.referrer_upi is not null order by r.created_at desc limit 1)) end
$$;

create or replace function public.client_set_referral_upi(p_upi text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if private.client_phone10() is null then raise exception 'Not signed in'; end if;
  if coalesce(p_upi, '') !~ '^[A-Za-z0-9._-]{2,}@[A-Za-z]{2,}$' then raise exception 'Enter a valid UPI ID, e.g. name@okicici'; end if;
  update public.referrals set referrer_upi = p_upi where referrer_phone10 = private.client_phone10() and status in ('joined', 'payable');
end $$;

-- 11. Admin actions -----------------------------------------------------------------------------
create or replace function public.admin_set_partner_status(p_id uuid, p_status text, p_manager uuid default null,
  p_model text default null) returns text
language plpgsql security definer set search_path = '' as $$
declare v_code text;
begin
  if not private.is_admin() then raise exception 'Admins only'; end if;
  if p_status not in ('pending', 'active', 'paused', 'rejected') then raise exception 'Bad status'; end if;
  select code into v_code from public.partners where id = p_id;
  if p_status = 'active' and v_code is null then
    v_code := 'LWP-' || lpad((select count(*) + 1 from public.partners where code is not null)::text, 4, '0');
  end if;
  update public.partners set status = p_status, code = v_code,
         manager_user_id = coalesce(p_manager, manager_user_id),
         model = coalesce(nullif(p_model, ''), model),
         approved_at = case when p_status = 'active' and approved_at is null then now() else approved_at end,
         approved_by = case when p_status = 'active' and approved_by is null then (select auth.uid()) else approved_by end
   where id = p_id;
  return v_code;
end $$;

create or replace function public.admin_mark_commissions_paid(p_partner uuid, p_ref text) returns integer
language plpgsql security definer set search_path = '' as $$
declare n integer;
begin
  if not private.is_admin() then raise exception 'Admins only'; end if;
  if coalesce(trim(p_ref), '') = '' then raise exception 'Enter the UPI / bank reference (UTR)'; end if;
  update public.partner_commissions set status = 'paid', payout_ref = left(trim(p_ref), 80), paid_at = now(),
         paid_by = (select auth.uid())
   where partner_id = p_partner and status = 'approved';
  get diagnostics n = row_count;
  return n;
end $$;

create or replace function public.admin_mark_referral_paid(p_id uuid, p_ref text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not private.is_admin() then raise exception 'Admins only'; end if;
  update public.referrals set status = 'paid', payout_ref = left(trim(p_ref), 80), paid_at = now()
   where id = p_id and status = 'payable';
  if not found then raise exception 'Not payable'; end if;
end $$;

revoke all on function public.partner_signup(text, text, text, text, text, text, text, text) from public, anon;
revoke all on function public.partner_dashboard() from public, anon;
revoke all on function public.partner_add_client(text, text, text[], text) from public, anon;
revoke all on function public.client_referral_info() from public, anon;
revoke all on function public.client_set_referral_upi(text) from public, anon;
revoke all on function public.admin_set_partner_status(uuid, text, uuid, text) from public, anon;
revoke all on function public.admin_mark_commissions_paid(uuid, text) from public, anon;
revoke all on function public.admin_mark_referral_paid(uuid, text) from public, anon;
grant execute on function public.partner_signup(text, text, text, text, text, text, text, text) to authenticated;
grant execute on function public.partner_dashboard() to authenticated;
grant execute on function public.partner_add_client(text, text, text[], text) to authenticated;
grant execute on function public.client_referral_info() to authenticated;
grant execute on function public.client_set_referral_upi(text) to authenticated;
grant execute on function public.admin_set_partner_status(uuid, text, uuid, text) to authenticated;
grant execute on function public.admin_mark_commissions_paid(uuid, text) to authenticated;
grant execute on function public.admin_mark_referral_paid(uuid, text) to authenticated;
