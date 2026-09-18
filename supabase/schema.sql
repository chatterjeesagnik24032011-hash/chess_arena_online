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


-- Worldwide random matchmaking. The first available waiting player is matched;
-- the second player always receives the opposite color. If nobody is waiting,
-- the caller creates a waiting room with a randomly assigned color.
create or replace function public.find_or_join_random_game(p_minutes integer default 10, p_increment integer default 0)
returns table(game_id uuid, color text, game_status text)
language plpgsql
security definer
set search_path = public
as $$
declare
  uid uuid := auth.uid();
  g public.games%rowtype;
  assigned_color text;
begin
  if uid is null then
    raise exception 'You must be logged in to use random matchmaking.';
  end if;
  if p_minutes < 1 or p_minutes > 180 then
    raise exception 'Invalid time control.';
  end if;
  if p_increment < 0 or p_increment > 3600 then
    raise exception 'Invalid increment.';
  end if;

  -- Reuse the caller's own waiting room instead of creating duplicates.
  select gg.* into g
  from public.games as gg
  where gg.status = 'waiting'
    and (gg.white_id = uid or gg.black_id = uid)
  order by gg.created_at asc
  limit 1;
  if found then
    if g.white_id = uid then
      return query select g.id, 'white'::text, g.status::text;
    else
      return query select g.id, 'black'::text, g.status::text;
    end if;
    return;
  end if;

  -- Lock one available room so two users cannot claim the same slot.
  select gg.* into g
  from public.games as gg
  where gg.status = 'waiting'
    and (gg.white_id is null or gg.black_id is null)
    and gg.white_id is distinct from uid
    and gg.black_id is distinct from uid
  order by gg.created_at asc
  for update skip locked
  limit 1;

  if found then
    if g.white_id is null then
      update public.games as ug
      set white_id = uid, status = 'active', updated_at = now()
      where ug.id = g.id;
      return query select g.id, 'white'::text, 'active'::text;
    else
      update public.games as ug
      set black_id = uid, status = 'active', updated_at = now()
      where ug.id = g.id;
      return query select g.id, 'black'::text, 'active'::text;
    end if;
    return;
  end if;

  assigned_color := case when random() < 0.5 then 'white' else 'black' end;
  if assigned_color = 'white' then
    insert into public.games(white_id, status, fen, moves, white_time, black_time, increment)
    values(uid, 'waiting', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', '[]'::jsonb, p_minutes*60000, p_minutes*60000, p_increment)
    returning id into g.id;
  else
    insert into public.games(black_id, status, fen, moves, white_time, black_time, increment)
    values(uid, 'waiting', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', '[]'::jsonb, p_minutes*60000, p_minutes*60000, p_increment)
    returning id into g.id;
  end if;

  return query select g.id, assigned_color, 'waiting'::text;
end;
$$;

revoke all on function public.find_or_join_random_game(integer, integer) from public;
grant execute on function public.find_or_join_random_game(integer, integer) to authenticated;
