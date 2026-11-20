-- 20 Nov 2026: remember a client's referral UPI even before their first referral.
-- Before: client_set_referral_upi() only updated existing referral rows, so a UPI saved early was lost.
-- Now: it is stored per mobile number in public.client_referral_upi (private to the client and Admins),
-- copied onto existing open referrals, and onto every new referral when it is created.
-- Impact on existing data: none (adds one table and a trigger; the two functions keep their signatures).
begin;

create table if not exists public.client_referral_upi (
  phone10 text primary key,
  upi text not null,
  updated_at timestamptz not null default now()
);
alter table public.client_referral_upi enable row level security;
drop policy if exists cru_admin_read on public.client_referral_upi;
create policy cru_admin_read on public.client_referral_upi for select to authenticated using (private.is_admin());

create or replace function public.client_set_referral_upi(p_upi text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if private.client_phone10() is null then raise exception 'Not signed in'; end if;
  if coalesce(p_upi, '') !~ '^[A-Za-z0-9._-]{2,}@[A-Za-z]{2,}$' then raise exception 'Enter a valid UPI ID, e.g. name@okicici'; end if;
  insert into public.client_referral_upi (phone10, upi) values (private.client_phone10(), p_upi)
  on conflict (phone10) do update set upi = excluded.upi, updated_at = now();
  update public.referrals set referrer_upi = p_upi where referrer_phone10 = private.client_phone10() and status in ('joined', 'payable');
end $$;

create or replace function private.referral_fill_upi() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if new.referrer_upi is null then
    select upi into new.referrer_upi from public.client_referral_upi where phone10 = new.referrer_phone10;
  end if;
  return new;
end $$;
drop trigger if exists referral_fill_upi on public.referrals;
create trigger referral_fill_upi before insert on public.referrals for each row execute function private.referral_fill_upi();

create or replace function public.client_referral_info() returns jsonb
language sql stable security definer set search_path = '' as $$
  select case when private.client_phone10() is null then null else jsonb_build_object(
    'code', 'LWR-' || right(private.client_phone10(), 6),
    'reward', private.setting_num('referral_reward_amount', 0),
    'reward_pct', private.setting_num('referral_reward_pct', 0),
    'referrals', coalesce((select jsonb_agg(jsonb_build_object('date', r.created_at, 'status', r.status,
                   'reward', r.reward_amount, 'paid_at', r.paid_at) order by r.created_at desc)
                 from public.referrals r where r.referrer_phone10 = private.client_phone10()), '[]'::jsonb),
    'upi', (select u.upi from public.client_referral_upi u where u.phone10 = private.client_phone10())) end
$$;

commit;
