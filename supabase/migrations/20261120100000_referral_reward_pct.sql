-- 20 Nov 2026 (Kunal): client referral reward = 10% of our professional fee, paid to the client's UPI.
-- Adds setting referral_reward_pct = 10 and uses it when referral_reward_amount (flat) is 0.
-- The reward is worked out on the referred client's first payment, from the professional-fee part of it.
-- Impact on existing data: none (no referrals are payable yet). Only the trigger function body
-- and client_referral_info() change; client_referral_info() also returns reward_pct for the portal.
begin;
insert into private.app_settings (key, value) values ('referral_reward_pct', '10')
on conflict (key) do update set value = excluded.value;

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
  -- Flat amount if set (> 0), otherwise referral_reward_pct % of our professional fee in this payment.
  v_reward := private.setting_num('referral_reward_amount', 0);
  if v_reward <= 0 then
    v_reward := round(coalesce(nullif(new.professional_fees_amount, 0),
                        case when new.payment_component = 'professional_fees' then new.amount else 0 end)
                      * private.setting_num('referral_reward_pct', 0) / 100, 2);
  end if;
  update public.referrals set status = 'payable', reward_amount = v_reward
   where referred_lead_id = l.id and status = 'joined' and v_reward > 0;
  return new;
end $$;

create or replace function public.client_referral_info() returns jsonb
language sql stable security definer set search_path = '' as $$
  select case when private.client_phone10() is null then null else jsonb_build_object(
    'code', 'LWR-' || right(private.client_phone10(), 6),
    'reward', private.setting_num('referral_reward_amount', 0),
    'reward_pct', private.setting_num('referral_reward_pct', 0),
    'referrals', coalesce((select jsonb_agg(jsonb_build_object('date', r.created_at, 'status', r.status,
                   'reward', r.reward_amount, 'paid_at', r.paid_at) order by r.created_at desc)
                 from public.referrals r where r.referrer_phone10 = private.client_phone10()), '[]'::jsonb),
    'upi', (select r.referrer_upi from public.referrals r where r.referrer_phone10 = private.client_phone10()
             and r.referrer_upi is not null order by r.created_at desc limit 1)) end
$$;

commit;
