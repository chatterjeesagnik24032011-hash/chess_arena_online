CHESS ARENA v5 — SMOOTH EDITION

Features:
- Smooth 60 FPS Pygame UI.
- Background-threaded Stockfish thinking and move analysis so the board does not freeze.
- Beginner, Minimax, Magnus-style Stockfish profile, and full Stockfish opponent choices.
- Top 10 Stockfish candidate moves on review, plus a separate best-move search.
- Chess.com-style labels: BOOK MOVE, BEST MOVE, BRILLIANT MOVE, GREAT MOVE, EXCELLENT MOVE, GOOD MOVE, INACCURACY, MISTAKE, BLUNDER.
- Check/checkmate sounds generated at runtime; no sound files required.
- Hint mode, undo, board flip, pause, PGN saving, evaluation bar, clocks, move highlighting.
- Stockfish path is auto-detected inside the project; otherwise set STOCKFISH_PATH or use the Stockfish executable beside the app.

Install:
  pip install -r requirements.txt
Run:
  python main.py

Controls:
B choose bot | N new game | U undo | F flip | H hint | R review | S save PGN | P pause | M sound | Esc quit

Magnus mode is a strong Stockfish configuration, not an implementation of Magnus Carlsen.
The move labels are local heuristics inspired by common chess-site classifications; they are not an official Chess.com clone.
