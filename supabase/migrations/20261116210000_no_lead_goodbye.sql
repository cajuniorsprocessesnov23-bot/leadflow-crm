-- Goodbye message to "Clear no lead" clients (16 Nov 2026, owner decision).
-- When a lead moves to Clear no lead (including "Dropped – not interested" at follow-up),
-- the client gets one polite WhatsApp (template lw_c_no_lead): thanks, and contact us later.
-- Only new changes from now on (no backlog). Not sent when:
--   - the client has no WhatsApp consent (this also covers the "Not interested" button,
--     which turns consent off), or
--   - the lost reason is "Wrong number" or "Duplicate lead".
-- The trigger is named so it runs after wa_cancel_on_optout (triggers fire in name order),
-- so the cancel step never skips this message. whatsapp-dispatch allows message key
-- C-nolead for Clear no lead leads. Nothing goes out until Meta approves lw_c_no_lead.
-- Impact on existing data: none.

create or replace function private.wa_no_lead_message() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if new.stage = 'Clear no lead' and new.stage is distinct from old.stage
     and new.whatsapp_opt_in
     and coalesce(new.lost_reason, '') not in ('Wrong number', 'Duplicate lead') then
    perform private.wa_enqueue(new.id, new.phone, 'client', null, 'C-nolead', 'lw_c_no_lead',
      jsonb_build_array(coalesce(nullif(trim(new.name), ''), 'there')), 'NL:' || new.id);
  end if;
  return new;
end $$;

drop trigger if exists wa_no_lead_message on public.leads;
create trigger wa_no_lead_message after update on public.leads
  for each row execute function private.wa_no_lead_message();
