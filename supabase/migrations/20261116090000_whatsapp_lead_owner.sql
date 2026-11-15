-- WhatsApp lead owner setting
-- New WhatsApp enquiries (a number not yet in the CRM) become Unverified leads owned by ONE chosen
-- team member. The Super Admin picks that person in Manage Users. Default: Riya.
--
-- What this adds:
--   1. Setting 'whatsapp_lead_owner' in private.app_settings (a user id). Seeded with Riya's account.
--   2. public.get_whatsapp_lead_owner()  -> the chosen user id (signed-in users and the webhook can read it).
--   3. public.set_whatsapp_lead_owner(id) -> Super Admin only; the id must be an existing team member.
-- Impact on existing data: none. No leads are changed; only future WhatsApp leads use the setting.
-- If the setting is empty or the person was removed, the webhook falls back to the staff member with
-- the fewest WhatsApp leads.

insert into private.app_settings (key, value)
select 'whatsapp_lead_owner', coalesce((
  select ur.user_id::text
  from public.user_roles ur join auth.users u on u.id = ur.user_id
  where coalesce(u.raw_user_meta_data->>'full_name', '') ilike 'riya%' or u.email ilike 'riya%'
  order by u.created_at limit 1), '')
on conflict (key) do nothing;

create or replace function public.get_whatsapp_lead_owner()
returns uuid language sql stable security definer set search_path to '' as $$
  select nullif(value, '')::uuid from private.app_settings where key = 'whatsapp_lead_owner'
$$;

create or replace function public.set_whatsapp_lead_owner(p_user_id uuid)
returns uuid language plpgsql security definer set search_path to '' as $$
begin
  if not private.is_super_admin() then
    raise exception 'Only the Super Admin can change who gets WhatsApp leads';
  end if;
  if not exists (select 1 from public.user_roles where user_id = p_user_id) then
    raise exception 'That person is not a team member';
  end if;
  insert into private.app_settings (key, value, updated_at) values ('whatsapp_lead_owner', p_user_id::text, now())
  on conflict (key) do update set value = excluded.value, updated_at = now();
  return p_user_id;
end $$;

revoke all on function public.get_whatsapp_lead_owner() from public, anon;
revoke all on function public.set_whatsapp_lead_owner(uuid) from public, anon;
grant execute on function public.get_whatsapp_lead_owner() to authenticated, service_role;
grant execute on function public.set_whatsapp_lead_owner(uuid) to authenticated;
