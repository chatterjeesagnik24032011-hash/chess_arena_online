import os, threading, queue, time
from pathlib import Path
import pygame, chess, chess.pgn
from engine import EngineManager
from review import MoveReview
from gui import ChessGUI
from timer import ChessTimer

FPS = 60

class App:
    def __init__(self):
        pygame.init()
        try: pygame.mixer.init()
        except pygame.error: pass
        self.gui = ChessGUI()
        self.engine = EngineManager()
        self.review = MoveReview()
        self.timer = ChessTimer(10, 0)
        self.board = chess.Board()
        self.bot = "Minimax"
        self.human_color = chess.WHITE
        self.time_control = "10 + 0"
        self.theme = "Classic"
        self.running = True
        self.ai_busy = False
        self.analysis_busy = False
        self.tasks = queue.Queue()
        self.results = queue.Queue()
        self.worker = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker.start()
        self.status = "Your move"
        self.last_move = None
        self.last_label = ""
        self.hint = None
        self.eval_cp = 0
        self.eval_text = "0.00"
        self.move_history = []
        self.pending_review = None
        self.sound_enabled = True
        self.paused = False

    def worker_loop(self):
        while True:
            kind, payload = self.tasks.get()
            if kind == "quit": return
            try:
                if kind == "ai":
                    move = self.engine.choose_move(payload[0], payload[1])
                    self.results.put(("ai", move))
                elif kind == "analyze_move":
                    before, played, bot = payload
                    data = self.engine.analyze_move(before, played, bot)
                    self.results.put(("analysis", data))
                elif kind == "hint":
                    board, bot = payload
                    data = self.engine.analyze(board, bot, time_limit=0.5, depth=18, multipv=3)
                    self.results.put(("hint", data))
            except Exception as exc:
                self.results.put(("error", str(exc)))

    def queue_ai(self):
        if self.ai_busy or self.board.is_game_over() or self.board.turn == self.human_color or self.paused: return
        self.ai_busy = True
        self.status = f"{self.bot} is thinking..."
        self.tasks.put(("ai", (self.board.copy(), self.bot)))

    def queue_analysis(self, before, played):
        self.analysis_busy = True
        self.tasks.put(("analyze_move", (before, played, self.bot)))

    def new_game(self):
        self.board = chess.Board(); self.review = MoveReview(); self.timer.reset()
        self.last_move = None; self.last_label = ""; self.hint = None; self.eval_cp = 0; self.eval_text = "0.00"
        self.move_history = []; self.status = "Your move" if self.board.turn == self.human_color else f"{self.bot} is thinking..."; self.ai_busy = False; self.analysis_busy = False; self.gui.selected = None; self.gui.legal = []

    def make_move(self, move, is_human=True):
        if move not in self.board.legal_moves: return False
        before = self.board.copy()
        san = self.board.san(move)
        self.board.push(move)
        self.last_move = move
        self.move_history.append((before, move, san))
        moved_color = before.turn
        self.timer.switch()
        self.timer.add_increment(moved_color)
        self.play_sound(checkmate=self.board.is_checkmate(), check=self.board.is_check())
        if is_human:
            self.queue_analysis(before, move)
        self.hint = None
        return True

    def play_sound(self, checkmate=False, check=False):
        if not self.sound_enabled: return
        try:
            import array, math
            rate = 44100
            duration = 0.20 if not checkmate else 0.42
            freqs = [880, 1175] if checkmate else ([660, 880] if check else [520])
            buf = array.array('h')
            n = int(rate * duration)
            for i in range(n):
                t = i / rate
                f = freqs[int(t * len(freqs) / duration) % len(freqs)]
                env = min(1.0, i / 500) * min(1.0, (n-i) / 2000)
                val = int(11000 * env * math.sin(2*math.pi*f*t))
                buf.append(val); buf.append(val)
            snd = pygame.mixer.Sound(buffer=buf.tobytes()); snd.play()
        except Exception:
            pass

    def process_results(self):
        while True:
            try: kind, data = self.results.get_nowait()
            except queue.Empty: break
            if kind == "ai":
                self.ai_busy = False
                if data and data in self.board.legal_moves and not self.paused:
                    self.make_move(data, is_human=False)
                    self.status = "Your move" if not self.board.is_game_over() else self.game_status()
            elif kind == "analysis":
                self.analysis_busy = False
                self.review.add_analysis(data)
                self.last_label = data["label"]
                self.eval_cp = data["played_cp"]
                self.eval_text = self.format_eval(data["played_cp"])
            elif kind == "hint":
                self.hint = data
            elif kind == "error":
                self.ai_busy = False; self.analysis_busy = False; self.status = f"Engine error: {data[:50]}"

    @staticmethod
    def format_eval(cp):
        if abs(cp) >= 90000: return "#" + ("+" if cp > 0 else "-")
        return f"{cp/100:+.2f}"

    def game_status(self):
        if self.board.is_checkmate(): return "Checkmate"
        if self.board.is_stalemate(): return "Stalemate"
        if self.board.is_insufficient_material(): return "Draw — insufficient material"
        if self.board.can_claim_threefold_repetition(): return "Draw claim available"
        return "Game over"

    def undo(self):
        if not self.move_history: return
        # Remove bot + human pair when possible.
        count = 2 if len(self.move_history) >= 2 else 1
        for _ in range(count):
            if self.move_history:
                self.move_history.pop(); self.board.pop()
        self.last_move = self.board.peek() if self.board.move_stack else None
        self.review.undo_last(count); self.status = "Your move"; self.ai_busy = False; self.analysis_busy = False

    def save_pgn(self):
        game = chess.pgn.Game(); game.headers["Event"] = "Chess Arena"; game.headers["White"] = "Player"; game.headers["Black"] = self.bot
        node = game
        for _, move, _ in self.move_history: node = node.add_variation(move)
        path = Path.cwd() / f"chess_arena_{time.strftime('%Y%m%d_%H%M%S')}.pgn"
        path.write_text(str(game), encoding="utf-8")
        self.status = f"Saved {path.name}"

    def handle(self, event):
        if event.type == pygame.QUIT: self.running = False; return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self.running = False
            elif event.key == pygame.K_n: self.new_game()
            elif event.key == pygame.K_b:
                old_bot = self.bot
                chosen = self.gui.choose_bot(self.bot)
                if chosen != old_bot:
                    self.bot = chosen; self.new_game(); self.status = f"Opponent changed to {self.bot}"
            elif event.key == pygame.K_t:
                chosen = self.gui.choose_theme(self.theme)
                if chosen != self.theme: self.theme = chosen; self.status = f"Theme: {self.theme}"
            elif event.key == pygame.K_c:
                chosen = self.gui.choose_time(self.time_control)
                if chosen != self.time_control:
                    self.time_control = chosen; parts=chosen.split(); minutes=int(parts[0]); increment=int(parts[2]); self.timer=ChessTimer(minutes, increment); self.status=f"Clock: {self.time_control}"
            elif event.key == pygame.K_a:
                chosen = self.gui.choose_side(self.human_color)
                new_color = chess.WHITE if chosen == 'White' else chess.BLACK
                if new_color != self.human_color:
                    self.human_color = new_color; self.new_game(); self.status=f"You play {chosen}"
            elif event.key == pygame.K_u: self.undo()
            elif event.key == pygame.K_f: self.gui.flipped = not self.gui.flipped
            elif event.key == pygame.K_h and not self.ai_busy and not self.analysis_busy:
                self.tasks.put(("hint", (self.board.copy(), self.bot)))
            elif event.key == pygame.K_r: self.gui.show_review(self.review, self.engine)
            elif event.key == pygame.K_s: self.save_pgn()
            elif event.key == pygame.K_p: self.paused = not self.paused; self.status = "Paused" if self.paused else "Your move"
            elif event.key == pygame.K_m: self.sound_enabled = not self.sound_enabled
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Clickable bot selector in the right panel.
            mx, my = event.pos
            if mx >= self.gui.BOARD and 55 <= my <= 105:
                chosen = self.gui.choose_bot(self.bot)
                if chosen != self.bot:
                    self.bot = chosen
                    self.new_game()
                    self.status = f"Playing vs {self.bot}"
                return
            move = self.gui.board_click(self.board)
            if move and self.board.turn == self.human_color and not self.ai_busy and not self.analysis_busy and not self.paused:
                self.make_move(move, is_human=True)
                self.status = "Analyzing your move..."

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get(): self.handle(event)
            self.process_results()
            self.timer.update(self.board.turn if not self.paused else None)
            if self.timer.winner_by_time() is not None: self.status = "Time — " + ("White wins" if self.timer.winner_by_time() == chess.WHITE else "Black wins")
            if self.board.is_game_over(): self.status = self.game_status()
            self.queue_ai()
            self.gui.theme = self.theme
            self.gui.draw(self.board, self.bot, self.status, self.timer, self.last_move, self.last_label, self.review, self.hint, self.eval_cp, self.sound_enabled, self.paused, self.human_color, self.time_control)
            clock.tick(FPS)
        self.tasks.put(("quit", None)); self.engine.close(); pygame.quit()

if __name__ == "__main__": App().run()
