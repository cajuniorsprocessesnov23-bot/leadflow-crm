-- Missed-call WhatsApp for follow-up calls (16 Nov 2026, owner request: "follow up messages didn't go").
-- Until now the missed-call message (lw_c2_missed_call, sent as lw_c2_missed_call_u) only went for
-- first verification calls (Unverified / Not picked up stages). Follow-up calls on Verified or
-- Work dropped leads sent nothing.
-- What this adds: when staff log a call with outcome "Not picked up" (call_activity) on a lead that
-- is Verified or Work dropped, the client gets the missed-call message once that day.
-- The CRM gets a "Not picked up" button for follow-up calls (same stage, next follow-up date).
-- Not sent without WhatsApp consent. Impact on existing data: none.

create or replace function private.wa_followup_missed_call() returns trigger
language plpgsql security definer set search_path = '' as $$
declare l public.leads%rowtype;
begin
  if new.outcome <> 'Not picked up' or new.lead_id is null then return new; end if;
  select * into l from public.leads where id = new.lead_id;
  if not found or not l.whatsapp_opt_in or l.stage not in ('Verified', 'Work dropped') then return new; end if;
  perform private.wa_enqueue(l.id, l.phone, 'client', null, 'C2', 'lw_c2_missed_call',
    jsonb_build_array(coalesce(nullif(trim(l.name), ''), 'there'),
                      coalesce(nullif(array_to_string(l.lead_types, ', '), ''), 'your requirement')),
    'C2:' || l.id || ':' || (now() at time zone 'Asia/Kolkata')::date);
  return new;
end $$;

drop trigger if exists wa_followup_missed_call on public.call_activity;
create trigger wa_followup_missed_call after insert on public.call_activity
  for each row execute function private.wa_followup_missed_call();
