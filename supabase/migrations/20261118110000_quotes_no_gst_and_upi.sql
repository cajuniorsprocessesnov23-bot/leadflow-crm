-- 18 Nov 2026 (Kunal): "GST still not applicable"; UPI ID cajuniorsknn@okaxis.
-- 1. New quotes default to 0% GST (no GST line). Staff can still enter a rate later if you register.
-- 2. Company UPI ID saved in settings. The client portal already shows "Pay by UPI" when it is set.
-- Impact: no existing quotes yet; only the default and one setting change.
alter table public.quotes alter column gst_rate set default 0;
update public.quotes set gst_rate = 0 where status in ('draft', 'pending_approval');
update private.app_settings set value = 'cajuniorsknn@okaxis' where key = 'upi_id';
select key, value from private.app_settings where key = 'upi_id';
