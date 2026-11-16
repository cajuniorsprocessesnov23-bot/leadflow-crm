-- Enquiry page tracking (16 Nov 2026)
-- What this adds:
--   web_events: one row per enquiry-page event (visit, form_start, form_submit, call_tap, wa_tap)
--   with the ad source / campaign / service from the link. No names or phone numbers are stored.
--   Written only by the web-lead Edge Function (service role); Admins can read it for
--   Reports → Sources → "Ad funnel". Nobody else can read or change it.
-- Impact on existing data: none (new empty table).
create table if not exists public.web_events (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  event text not null check (event in ('visit', 'form_start', 'form_submit', 'call_tap', 'wa_tap')),
  source text not null default '',
  campaign text not null default '',
  service text not null default '',
  session_id text not null default '',
  has_click_id boolean not null default false,
  device text not null default ''
);
create index if not exists web_events_created_idx on public.web_events (created_at desc);
alter table public.web_events enable row level security;
drop policy if exists web_events_admin_read on public.web_events;
create policy web_events_admin_read on public.web_events for select to authenticated using ((select private.is_admin()));
