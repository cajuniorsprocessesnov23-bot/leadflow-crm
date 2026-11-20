-- 20 Nov 2026: public 'site' bucket for website images (applied via the dashboard SQL editor).
-- Anyone can view the images; only CRM staff (private.is_staff()) can upload, replace or list them.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('site','site',true,800000,array['image/webp','image/png','image/jpeg'])
on conflict (id) do nothing;
drop policy if exists site_staff_insert on storage.objects;
create policy site_staff_insert on storage.objects for insert to authenticated with check (bucket_id = 'site' and private.is_staff());
drop policy if exists site_staff_update on storage.objects;
create policy site_staff_update on storage.objects for update to authenticated using (bucket_id = 'site' and private.is_staff());
drop policy if exists site_staff_select on storage.objects;
create policy site_staff_select on storage.objects for select to authenticated using (bucket_id = 'site' and private.is_staff());
