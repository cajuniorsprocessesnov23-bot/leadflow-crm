-- 20 Nov 2026: the WhatsApp quote template lw_c_quote is submitted with a "View quote" link button and
-- no document header (a document header needs a sample file uploaded to Meta). The PDF is one tap away
-- on the quote page. So approve_quote() no longer sends header_document (sending it to a template without
-- a header would make Meta reject the message). Impact: none on data; no quotes have been approved yet.
begin;
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
        'button_url', q.public_token::text),
      'CQ:' || q.id);
  end if;
  return jsonb_build_object('ok', true, 'quote_no', q.quote_no, 'whatsapp', l.whatsapp_opt_in);
end $$;
commit;
