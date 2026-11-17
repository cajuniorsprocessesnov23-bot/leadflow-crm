-- Price list and timelines per service, edited by Admins / Super Admin in CRM → Tools → Settings.
-- Used by the new website (instant quote, price calculator) and the client portal.
--
-- Adds to lead_type_options (one row per service):
--   govt_fee          numeric  government / statutory fee in ₹ (null = not shown)
--   professional_fee  numeric  Legal Wegal fee in ₹ (null = not shown)
--   price_note        text     short note, e.g. "+ GST", "per class", "starting from"
--   timeline          text     what the client sees, e.g. "3–7 working days"
--   show_on_website   boolean  default true
-- Visitors on the website (not logged in) may read active services with these fields.
-- Impact: none on existing data. Write access stays exactly as today (Admin and Super Admin only).

alter table public.lead_type_options
  add column if not exists govt_fee numeric(12,2) check (govt_fee is null or govt_fee >= 0),
  add column if not exists professional_fee numeric(12,2) check (professional_fee is null or professional_fee >= 0),
  add column if not exists price_note text not null default '',
  add column if not exists timeline text not null default '',
  add column if not exists show_on_website boolean not null default true;

drop policy if exists "Website visitors can read active services" on public.lead_type_options;
create policy "Website visitors can read active services" on public.lead_type_options
  for select to anon using (active and show_on_website);
