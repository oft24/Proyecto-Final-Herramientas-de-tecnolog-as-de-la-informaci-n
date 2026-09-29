-- Harden the public Data API to the minimum surface used by this app.
-- The catalog is intentionally public-readable and writable only by database owners.

-- Future objects created by migrations must be explicitly exposed.
alter default privileges for role postgres in schema public
  revoke all privileges on tables from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
  revoke all privileges on sequences from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
  revoke execute on functions from public, anon, authenticated, service_role;

-- Existing catalog: keep public reads, remove every direct write/admin capability.
alter table public.products enable row level security;
alter table public.products force row level security;

revoke all privileges on table public.products
  from anon, authenticated, service_role;

grant select on table public.products
  to anon, authenticated;

-- Trigger helpers are internal implementation details, not RPC endpoints.
revoke execute on function public.set_updated_at()
  from public, anon, authenticated, service_role;
