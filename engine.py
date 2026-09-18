import os, shutil, threading
from pathlib import Path
import chess
import chess.engine

class EngineManager:
    def __init__(self):
        self.stockfish_path = self.find_stockfish()
        self.engine = None
        self.lock = threading.RLock()
        self.depth = 24

    def find_stockfish(self):
        candidates=[]
        env=os.getenv("STOCKFISH_PATH")
        if env: candidates.append(env)
        names=("stockfish-windows-x86-64-universal.exe","stockfish-windows-x86-64-avx2.exe","stockfish.exe","stockfish")
        for name in names:
            found=shutil.which(name)
            if found: candidates.append(found)
        root=Path(__file__).resolve().parent
        for name in names:
            p=root/name
            if p.exists(): candidates.append(str(p))
        for p in root.rglob("stockfish*.exe"): candidates.append(str(p))
        for p in root.rglob("stockfish"):
            if p.is_file(): candidates.append(str(p))
        for p in candidates:
            try:
                if Path(p).is_file(): return str(Path(p).resolve())
            except OSError: pass
        return None

    def open(self):
        if not self.stockfish_path: return None
        with self.lock:
            if self.engine is None:
                self.engine=chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                threads=max(1,min(8,(os.cpu_count() or 4)-1))
                try: self.engine.configure({"Threads":threads,"Hash":512})
                except Exception: pass
            return self.engine

    def close(self):
        with self.lock:
            if self.engine:
                try: self.engine.quit()
                except Exception: pass
                self.engine=None

    def choose_move(self, board, bot):
        if bot=="Beginner":
            import random
            return random.choice(list(board.legal_moves)) if board.legal_moves else None
        if bot=="Minimax": return self.fallback(board,3)
        eng=self.open()
        if eng:
            limit=chess.engine.Limit(time=1.2 if bot=="Stockfish" else 4.0, depth=24 if bot=="Stockfish" else 32)
            opts={"Skill Level":20}
            if bot=="Magnus": opts.update({"Threads":max(1,min(8,(os.cpu_count() or 4)-1)),"Hash":512})
            try:
                with self.lock: return eng.play(board,limit,options=opts).move
            except Exception: pass
        return self.fallback(board,4 if bot=="Stockfish" else 5)

    def analyze(self, board, bot="Stockfish", time_limit=0.8, depth=24, multipv=10):
        eng=self.open()
        if eng:
            try:
                with self.lock:
                    infos=eng.analyse(board,chess.engine.Limit(time=time_limit,depth=depth),multipv=multipv)
                out=[]
                for info in infos:
                    score=info["score"].pov(board.turn); cp=score.score(mate_score=100000); pv=info.get("pv",[])
                    out.append({"move":pv[0] if pv else None,"cp":cp,"mate":score.mate(),"depth":info.get("depth",depth),"pv":pv[:8]})
                return out
            except Exception: pass
        m=self.fallback(board,4)
        return [{"move":m,"cp":0,"mate":None,"depth":4,"pv":[m] if m else []}]

    def analyze_move(self,before,played,bot):
        # MultiPV 10 is used for ranking; the best move is independently searched so MultiPV does not weaken it.
        top=self.analyze(before,"Stockfish",1.15,26,10)
        best=top[0] if top else {"move":played,"cp":0,"mate":None,"depth":0,"pv":[played]}
        eng=self.open(); played_cp=best.get("cp",0)
        after=before.copy(); after.push(played)
        if eng:
            try:
                with self.lock:
                    info=eng.analyse(after,chess.engine.Limit(time=1.0,depth=24))
                opp=info["score"].pov(after.turn); played_cp=-opp.score(mate_score=100000)
            except Exception: pass
        best_cp=best.get("cp",0); loss=max(0,best_cp-played_cp)
        label=self.classify(before,played,best.get("move"),loss,top)
        rank=next((i+1 for i,x in enumerate(top) if x.get("move")==played),None)
        return {"move":played,"best":best.get("move"),"best_cp":best_cp,"played_cp":played_cp,"loss":loss,"label":label,"top":top,"depth":best.get("depth",0),"rank":rank,"before_fen":before.fen(),"after_fen":after.fen()}

    def classify(self, board, move, best, loss, top):
        # Keep BEST separate from GREAT: matching the engine's top move is BEST,
        # while GREAT is reserved for a very close alternative that is not the
        # engine's exact first choice. This prevents every accurate move from
        # being shown as GREAT.
        if self.is_book(board, move):
            return "BOOK MOVE"

        rank = next((i + 1 for i, item in enumerate(top) if item.get("move") == move), 99)

        # Brilliant is intentionally rare: a non-best move must contain a
        # concrete tactical idea and lose almost nothing in the engine score.
        if move != best and board.is_capture(move) and board.gives_check(move) and loss <= 18:
            return "BRILLIANT MOVE"

        if move == best:
            return "BEST MOVE"

        if rank <= 2 and loss <= 10:
            return "GREAT MOVE"
        if rank <= 3 and loss <= 25:
            return "EXCELLENT MOVE"
        if rank <= 5 and loss <= 50:
            return "GOOD MOVE"
        if loss <= 100:
            return "INACCURACY"
        if loss <= 250:
            return "MISTAKE"
        return "BLUNDER"

    def is_book(self, board, move):
        # Small position-aware opening book for common first moves. It only marks
        # a move as BOOK when the preceding sequence matches a known opening line.
        lines = {
            (): {"e2e4", "d2d4", "c2c4", "g1f3"},
            ("e2e4",): {"e7e5", "c7c5", "e7e6", "c7c6", "g8f6"},
            ("e2e4", "e7e5"): {"g1f3", "f1c4", "d2d4"},
            ("e2e4", "e7e5", "g1f3"): {"b8c6", "g8f6", "d7d6"},
            ("e2e4", "e7e5", "g1f3", "b8c6"): {"f1b5", "f1c4", "d2d4"},
            ("e2e4", "c7c5"): {"g1f3", "b1c3", "c2c3"},
            ("e2e4", "c7c5", "g1f3"): {"d7d6", "b8c6", "e7e6"},
            ("d2d4",): {"d7d5", "g8f6", "g7g6", "e7e6"},
            ("d2d4", "d7d5"): {"c2c4", "g1f3", "c1f4", "c2c3"},
            ("d2d4", "g8f6"): {"c2c4", "c1f4", "g1f3"},
            ("c2c4",): {"e7e5", "g8f6", "e7e6", "c7c5"},
            ("g1f3",): {"d7d5", "g8f6", "c7c5", "e7e6"},
        }
        key = tuple(m.uci() for m in list(board.move_stack))
        allowed = lines.get(key)
        return move.uci() in allowed if allowed else False

    def fallback(self,board,depth):
        vals={chess.PAWN:100,chess.KNIGHT:320,chess.BISHOP:330,chess.ROOK:500,chess.QUEEN:900,chess.KING:0}
        def ev(b): return sum((1 if p.color else -1)*vals[p.piece_type] for p in b.piece_map().values())
        def mm(b,d,a,beta,maxi):
            if d==0 or b.is_game_over(): return ev(b),None
            best=(-10**9,None) if maxi else (10**9,None)
            for m in b.legal_moves:
                b.push(m); sc,_=mm(b,d-1,a,beta,not maxi); b.pop()
                if (maxi and sc>best[0]) or ((not maxi) and sc<best[0]): best=(sc,m)
                if maxi: a=max(a,sc)
                else: beta=min(beta,sc)
                if beta<=a: break
            return best
        return mm(board,depth,-10**9,10**9,board.turn==chess.WHITE)[1]
