create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.games (
  id uuid primary key default gen_random_uuid(),
  white_id uuid references auth.users(id) on delete set null,
  black_id uuid references auth.users(id) on delete set null,
  status text not null default 'waiting' check (status in ('waiting','active','finished','abandoned')),
  fen text not null,
  moves jsonb not null default '[]'::jsonb,
  white_time integer not null default 600000,
  black_time integer not null default 600000,
  increment integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.games enable row level security;

-- Add clock columns safely when upgrading an existing project.
alter table public.games add column if not exists white_time integer not null default 600000;
alter table public.games add column if not exists black_time integer not null default 600000;
alter table public.games add column if not exists increment integer not null default 0;

drop policy if exists "profiles are readable" on public.profiles;
drop policy if exists "users create own profile" on public.profiles;
drop policy if exists "users update own profile" on public.profiles;
drop policy if exists "players can read their games" on public.games;
drop policy if exists "users can create games" on public.games;
drop policy if exists "players can update games" on public.games;
drop policy if exists "players can join waiting games" on public.games;

create policy "profiles are readable" on public.profiles for select to authenticated using (true);
create policy "users create own profile" on public.profiles for insert to authenticated with check (auth.uid()=id);
create policy "users update own profile" on public.profiles for update to authenticated using (auth.uid()=id) with check (auth.uid()=id);

create policy "players can read their games" on public.games for select to authenticated
using (auth.uid()=white_id or auth.uid()=black_id or status='waiting');

create policy "users can create games" on public.games for insert to authenticated
with check (auth.uid()=white_id or auth.uid()=black_id);

create policy "players can join waiting games" on public.games for update to authenticated
using (status='waiting' and (white_id is null or black_id is null))
with check (auth.uid()=white_id or auth.uid()=black_id);

create policy "players can update games" on public.games for update to authenticated
using (auth.uid()=white_id or auth.uid()=black_id)
with check (auth.uid()=white_id or auth.uid()=black_id);

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname='supabase_realtime' and schemaname='public' and tablename='games'
  ) then
    alter publication supabase_realtime add table public.games;
  end if;
end $$;
