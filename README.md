# Chess Arena Online v2

Web version of Chess Arena using Vite + React + chess.js + Supabase. The browser contains the legal-move board, bot engine, evaluation bar, clocks and review system. Online multiplayer uses Supabase Realtime.

## Deploy
1. Keep `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in Vercel.
2. Run `supabase/schema.sql` in Supabase SQL Editor. This upgrades the existing `games` table with clocks and a join policy.
3. Commit/push this folder to the existing GitHub repository.
4. Vercel should auto-deploy.

## Notes
- Never put `SUPABASE_SECRET_KEY` in Vercel frontend variables.
- The bot engine is the browser-safe port of the Python minimax/evaluation approach. The UI is structured so a Stockfish WASM adapter can be added without changing the board/review flow.
- For a production competitive server, move authoritative online move validation to a Supabase Edge Function/RPC rather than trusting browser updates.


## Worldwide Random Matchmaking
Use **Join Random Player** to enter a shared matchmaking queue. The first waiting player gets a randomly assigned color; the next player is automatically assigned the opposite color. The queue is global to authenticated users using the same Supabase project. Run the updated `supabase/schema.sql` once to create the matchmaking RPC.


## Random match confirmation
Random matches now show the opponent display name and require each player to confirm before moves are enabled.
