# Chess Arena Online

A web version of Chess Arena with a dark Game Review style UI, online games, accounts, persistent PostgreSQL storage, and realtime move updates.

## Stack
- React + Vite
- chess.js for legal chess moves
- Supabase Auth + Postgres + Realtime
- Vercel for public hosting

## Important authentication note
Supabase Auth does not provide a safe username-only/password login by default. This starter uses email/password authentication plus a public display name. Do not implement your own password hashing in the browser.

## Setup
1. Create a Supabase project.
2. Open SQL Editor and run `supabase/schema.sql`.
3. In Authentication settings, configure email/password sign-in. For easiest testing, you can disable email confirmation; for a public launch, keep email confirmation enabled.
4. Copy `.env.example` to `.env.local` and add your Supabase Project URL and publishable key.
5. Run:
   npm install
   npm run dev
6. Open the local URL printed by Vite.

## Make it public
Push this folder to GitHub, import the repository into Vercel, and add the same `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` environment variables in Vercel. Deploy.

## Data persistence
Games, users, and move history are stored in Supabase Postgres. “Forever” cannot honestly be guaranteed: the project owner must keep the Supabase project active and maintain backups/retention. Supabase documents daily backups and point-in-time recovery on paid plans.

## Multiplayer
Create an online game and share its Game ID. The opponent joins the same game and moves are broadcast through Supabase Realtime. The database also stores the FEN and move list.

## Production hardening still recommended
For a competitive/public chess site, move validation should be moved to a server-side Edge Function or database function so a modified browser cannot submit illegal positions. Add rate limiting, abuse controls, draw/clock enforcement, and server-side game authority before treating the site as tournament-grade.
