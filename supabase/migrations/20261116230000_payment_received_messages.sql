-- Payment received messages (16 Nov 2026, "set messages for everything we discussed").
-- When a payment is recorded in the CRM (payment_collections insert via record_payment):
--   1. Kunal (super admin number) gets the approved team template lw_t4_payment_received:
--      amount, component, client, reference, recorded by, balance pending.
--   2. The client gets a thank-you receipt (lw_c_payment_received, submitted 16 Nov; held until
--      Meta approves it) if WhatsApp consent is on.
-- The payment row is inserted before the lead balance is reduced, so "balance pending" is
-- computed as old balance minus this payment.
-- Impact on existing data: none (only new payments trigger messages).

create or replace function private.wa_payment_received() returns trigger
language plpgsql security definer set search_path = '' as $$
declare l public.leads%rowtype; v_admin text := (select value from private.app_settings where key = 'super_admin_whatsapp');
  v_amt text := to_char(new.amount, 'FM99,99,99,990.00');
  v_comp text := case when coalesce(new.government_charges_amount, 0) > 0 then 'government charges' else 'professional fees' end;
begin
  select * into l from public.leads where id = new.lead_id;
  if not found then return new; end if;
  perform private.wa_enqueue(l.id, v_admin, 'super_admin', null, 'T4', 'lw_t4_payment_received',
    jsonb_build_array(v_amt, v_comp, coalesce(nullif(trim(l.name), ''), 'client'), coalesce(nullif(l.lead_code, ''), l.id),
      coalesce(nullif(new.created_by_name, ''), 'team'), to_char(greatest(coalesce(l.pending_payment, 0) - new.amount, 0), 'FM99,99,99,990.00')),
    'T4:' || new.id);
  if l.whatsapp_opt_in then
    perform private.wa_enqueue(l.id, l.phone, 'client', null, 'C-paid', 'lw_c_payment_received',
      jsonb_build_array(coalesce(nullif(trim(l.name), ''), 'there'), v_amt,
        coalesce(nullif(array_to_string(l.lead_types, ', '), ''), 'your'), to_char(greatest(coalesce(l.pending_payment, 0) - new.amount, 0), 'FM99,99,99,990.00')),
      'CP:' || new.id);
  end if;
  return new;
end $$;

drop trigger if exists wa_payment_received on public.payment_collections;
create trigger wa_payment_received after insert on public.payment_collections
  for each row execute function private.wa_payment_received();
