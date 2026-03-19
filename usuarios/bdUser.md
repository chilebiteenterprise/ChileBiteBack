-- ======================================================
-- EXTENSION PARA UUID
-- ======================================================

create extension if not exists "uuid-ossp";

-- ======================================================
-- TABLA DE PERFILES DE USUARIO
-- ======================================================

create table public.profiles (

id uuid primary key references auth.users(id) on delete cascade,

email text unique,

username text unique,

avatar_url text,

role text not null default 'user',

created_at timestamp with time zone default now()

);

-- ======================================================
-- RESTRICCION DE ROLES
-- ======================================================

alter table public.profiles
add constraint valid_roles
check (role in (
'user',
'restaurant_owner',
'moderator',
'admin'
));

-- ======================================================
-- INDICES PARA MEJOR RENDIMIENTO
-- ======================================================

create index idx_profiles_email
on public.profiles(email);

create index idx_profiles_username
on public.profiles(username);

create index idx_profiles_role
on public.profiles(role);

-- ======================================================
-- FUNCION PARA CREAR PERFIL AUTOMATICAMENTE
-- ======================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$

begin

insert into public.profiles (
id,
email,
avatar_url
)
values (
new.id,
new.email,
new.raw_user_meta_data ->> 'avatar_url'
);

return new;

end;

$$
;

-- ======================================================
-- TRIGGER CUANDO SE CREA USUARIO
-- ======================================================

create trigger on_auth_user_created

after insert on auth.users

for each row
execute procedure public.handle_new_user();

-- ======================================================
-- ROW LEVEL SECURITY
-- ======================================================

alter table public.profiles enable row level security;

-- ======================================================
-- POLITICAS DE SEGURIDAD
-- ======================================================

-- usuario puede ver su perfil

create policy "Users can view own profile"
on public.profiles
for select
using (auth.uid() = id);

-- usuario puede actualizar su perfil

create policy "Users can update own profile"
on public.profiles
for update
using (auth.uid() = id);

-- ======================================================
-- POLITICA PARA ADMIN
-- ======================================================

create policy "Admins can view all profiles"
on public.profiles
for select
using (
  exists (
    select 1
    from public.profiles
    where id = auth.uid()
    and role = 'admin'
  )
);
$$
