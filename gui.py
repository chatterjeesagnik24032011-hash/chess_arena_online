import pygame, chess
pygame.font.init()


class ChessGUI:
    W, H = 1120, 720
    BOARD = 640
    PANEL = 480
    THEMES = {
        'Classic': ((74, 74, 74), (48, 48, 48), (215, 170, 70)),
        'Blue': ((74, 103, 135), (42, 62, 82), (100, 190, 235)),
        'Green': ((88, 112, 78), (57, 77, 52), (220, 190, 80)),
        'Purple': ((105, 88, 120), (67, 55, 78), (220, 155, 230)),
        'Wood': ((190, 165, 125), (120, 82, 52), (245, 205, 100)),
        'Midnight': ((75, 82, 100), (38, 43, 55), (120, 190, 255)),
    }
    PANELC = (27, 29, 32)
    PANEL2 = (34, 36, 40)
    TEXT = (238, 238, 238)
    MUTED = (153, 158, 164)
    GREEN = (115, 185, 75)
    RED = (222, 86, 78)
    PIECES = {chess.PAWN: '♟', chess.KNIGHT: '♞', chess.BISHOP: '♝', chess.ROOK: '♜', chess.QUEEN: '♛', chess.KING: '♚'}

    LABEL_STYLE = {
        'BOOK MOVE': ('B', (205, 178, 135)),
        'BEST MOVE': ('✓', (111, 168, 88)),
        'BRILLIANT MOVE': ('!!', (66, 148, 220)),
        'GREAT MOVE': ('★', (118, 174, 213)),
        'EXCELLENT MOVE': ('!', (119, 174, 213)),
        'GOOD MOVE': ('👍', (130, 190, 84)),
        'INACCURACY': ('?!', (242, 191, 42)),
        'MISTAKE': ('?', (240, 157, 77)),
        'BLUNDER': ('✕', (224, 77, 70)),
    }

    def __init__(self):
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        pygame.display.set_caption('Chess Arena — Stockfish Edition')
        self.flipped = False
        self.selected = None
        self.legal = []
        self.theme = 'Classic'
        self.animation = None
        self.font = pygame.font.SysFont(['segoeuisymbol', 'dejavusans'], 58)
        self.ui = pygame.font.SysFont('arial', 18)
        self.big = pygame.font.SysFont('arial', 28, bold=True)
        self.small = pygame.font.SysFont('arial', 14)
        self.tiny = pygame.font.SysFont('arial', 12)

    @property
    def LIGHT(self): return self.THEMES[self.theme][0]
    @property
    def DARK(self): return self.THEMES[self.theme][1]
    @property
    def ACC(self): return self.THEMES[self.theme][2]

    def txt(self, s, pos, font=None, color=None):
        self.screen.blit((font or self.ui).render(str(s), True, color or self.TEXT), pos)

    def choose_bot(self, current):
        return self._menu('CHOOSE YOUR OPPONENT', ['Beginner', 'Minimax', 'Magnus', 'Stockfish'], current, 'Click or use arrows + Enter')

    def choose_side(self, current):
        return self._menu('CHOOSE YOUR SIDE', ['White', 'Black'], 'White' if current else 'Black', 'Change side and start a new game')

    def choose_theme(self, current):
        return self._menu('BOARD THEME', list(self.THEMES), current, 'Choose a board style')

    def choose_time(self, current):
        return self._menu('TIME CONTROL', ['1 + 0', '3 + 2', '5 + 3', '10 + 0', '15 + 10', '30 + 0'], current, 'Minutes + increment')

    def _menu(self, title, options, current, subtitle):
        idx = options.index(current) if current in options else 0
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return current
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return current
                    if e.key in (pygame.K_UP, pygame.K_LEFT): idx = (idx - 1) % len(options)
                    elif e.key in (pygame.K_DOWN, pygame.K_RIGHT): idx = (idx + 1) % len(options)
                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER): return options[idx]
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for j, option in enumerate(options):
                        rect = pygame.Rect(250, 145 + j * 72, 620, 56)
                        if rect.collidepoint(e.pos): return option
            self.screen.fill(self.PANELC)
            self.txt(title, (285, 55), self.big, self.ACC)
            self.txt(subtitle, (315, 100), self.ui, self.MUTED)
            for j, option in enumerate(options):
                rect = pygame.Rect(250, 145 + j * 72, 620, 56)
                selected = j == idx
                pygame.draw.rect(self.screen, self.ACC if selected else (55, 58, 64), rect, border_radius=10)
                self.txt(option, (275, 160 + j * 72), self.ui, (20, 20, 20) if selected else self.TEXT)
            self.txt('Enter = select   Esc = cancel', (410, 610), self.small, self.MUTED)
            pygame.display.flip()
            pygame.time.Clock().tick(60)

    def promotion_menu(self, color):
        options = ['Queen', 'Rook', 'Bishop', 'Knight']
        idx = 0
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return chess.QUEEN
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return chess.QUEEN
                    if e.key in (pygame.K_UP, pygame.K_LEFT): idx = (idx - 1) % 4
                    elif e.key in (pygame.K_DOWN, pygame.K_RIGHT): idx = (idx + 1) % 4
                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER): return [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT][idx]
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for j in range(4):
                        if pygame.Rect(360, 175 + j * 65, 400, 50).collidepoint(e.pos):
                            return [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT][j]
            self.screen.fill(self.PANELC)
            self.txt('CHOOSE PROMOTION', (380, 85), self.big, self.ACC)
            for j, option in enumerate(options):
                rect = pygame.Rect(360, 175 + j * 65, 400, 50)
                pygame.draw.rect(self.screen, self.ACC if j == idx else (55, 58, 64), rect, border_radius=8)
                self.txt(option, (390, 188 + j * 65), self.ui, (20, 20, 20) if j == idx else self.TEXT)
            pygame.display.flip()
            pygame.time.Clock().tick(60)

    def board_click(self, board):
        mx, my = pygame.mouse.get_pos()
        s = self.BOARD // 8
        if mx >= self.BOARD or my >= self.BOARD: return None
        f, r = mx // s, 7 - my // s
        if self.flipped: f, r = 7 - f, 7 - r
        sq = chess.square(f, r)
        if self.selected is None:
            piece = board.piece_at(sq)
            if piece and piece.color == board.turn:
                self.selected = sq
                self.legal = [m for m in board.legal_moves if m.from_square == sq]
            return None
        candidates = [m for m in self.legal if m.to_square == sq]
        if candidates:
            move = candidates[0]
            if len(candidates) > 1 and any(m.promotion for m in candidates):
                promo = self.promotion_menu(board.turn)
                move = next((m for m in candidates if m.promotion == promo), candidates[0])
            self.selected, self.legal = None, []
            return move
        piece = board.piece_at(sq)
        self.selected = sq if piece and piece.color == board.turn else None
        self.legal = [m for m in board.legal_moves if m.from_square == self.selected] if self.selected is not None else []
        return None

    def _sqxy(self, sq):
        s = self.BOARD // 8
        f, r = chess.square_file(sq), 7 - chess.square_rank(sq)
        if self.flipped: f, r = 7 - f, 7 - r
        return f * s, r * s

    def captured(self, board):
        start = {c: {pt: (8 if pt == chess.PAWN else 2 if pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK) else 1) for pt in range(1, 7)} for c in (chess.WHITE, chess.BLACK)}
        for piece in board.piece_map().values(): start[piece.color][piece.piece_type] -= 1
        return start

    def _draw_board(self, board, last=None, hint=None, selected=True, coords=True, review_mode=False):
        s = self.BOARD // 8
        light, dark = ((225, 226, 199), (78, 119, 157)) if review_mode else (self.LIGHT, self.DARK)
        for rank in range(8):
            for file in range(8):
                rf, rr = (file, rank) if not self.flipped else (7 - file, 7 - rank)
                pygame.draw.rect(self.screen, light if (file + rank) % 2 == 0 else dark, (rf * s, rr * s, s, s))
                if coords:
                    rank_text = str(8 - rank if not self.flipped else rank + 1)
                    file_text = chr(97 + file if not self.flipped else 104 - file)
                    self.txt(rank_text, (rf * s + 4, rr * s + 2), self.tiny, dark if (file + rank) % 2 == 0 else light)
                    if rank == 7:
                        self.txt(file_text, (rf * s + s - 14, rr * s + s - 16), self.tiny, dark if (file + rank) % 2 == 0 else light)
        if last:
            for sq in (last.from_square, last.to_square):
                xx, yy = self._sqxy(sq)
                pygame.draw.rect(self.screen, (218, 180, 74), (xx, yy, s, s), 5)
        if hint:
            move = hint[0].get('move') if hint else None
            if move:
                for sq in (move.from_square, move.to_square):
                    xx, yy = self._sqxy(sq)
                    pygame.draw.circle(self.screen, (235, 195, 64), (xx + s // 2, yy + s // 2), 11, 3)
        if selected:
            for move in self.legal:
                xx, yy = self._sqxy(move.to_square)
                pygame.draw.circle(self.screen, (225, 225, 225), (xx + s // 2, yy + s // 2), 8)
            if self.selected is not None:
                xx, yy = self._sqxy(self.selected)
                pygame.draw.rect(self.screen, self.ACC, (xx, yy, s, s), 4)
        for sq, piece in board.piece_map().items():
            xx, yy = self._sqxy(sq)
            glyph = self.PIECES[piece.piece_type]
            fill = (246, 246, 246) if piece.color else (25, 25, 25)
            outline = (15, 15, 15) if piece.color else (235, 235, 235)
            surf = self.font.render(glyph, True, fill)
            ox = xx + (s - surf.get_width()) // 2
            oy = yy + (s - surf.get_height()) // 2 - 3
            out = self.font.render(glyph, True, outline)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                self.screen.blit(out, (ox + dx, oy + dy))
            self.screen.blit(surf, (ox, oy))

    def draw(self, board, bot, status, timer, last, label, review, hint, eval_cp, sound, paused, human_color, time_control):
        self.screen.fill(self.PANELC)
        self._draw_board(board, last=last, hint=hint)
        self._draw_eval_bar(eval_cp)
        self.panel(board, bot, status, timer, label, review, eval_cp, sound, paused, human_color, time_control)
        pygame.display.flip()

    def _draw_eval_bar(self, eval_cp):
        x = self.BOARD + 12
        pygame.draw.rect(self.screen, (16, 17, 19), (x, 0, 18, self.BOARD))
        pct = max(0.03, min(0.97, 0.5 + eval_cp / 1200))
        pygame.draw.rect(self.screen, (232, 232, 232), (x, self.BOARD * (1 - pct), 18, self.BOARD * pct))
        pygame.draw.rect(self.screen, (62, 63, 66), (x, self.BOARD * (1 - pct), 18, self.BOARD * (1 - pct)))

    def classification_badge(self, label, center, radius=16):
        if not label: return
        icon, color = self.LABEL_STYLE.get(label, ('?', (150, 150, 150)))
        pygame.draw.circle(self.screen, color, center, radius)
        font = self.tiny if len(icon) > 1 else self.ui
        surf = font.render(icon, True, (250, 250, 250) if icon != 'B' else (35, 35, 35))
        self.screen.blit(surf, (center[0] - surf.get_width() // 2, center[1] - surf.get_height() // 2))

    def panel(self, board, bot, status, timer, label, review, eval_cp, sound, paused, human_color, time_control):
        x = self.BOARD + 42
        self.txt('CHESS ARENA', (x, 18), self.big, self.ACC)
        self.txt(f'Opponent: {bot}', (x, 57), self.ui, self.ACC)
        self.txt(f'You: {"White" if human_color else "Black"}   {time_control}', (x, 80), self.small, self.MUTED)
        self.txt(f'White  {timer.fmt(timer.white)}', (x, 103), self.big)
        self.txt(f'Black  {timer.fmt(timer.black)}', (x, 137), self.big)
        self.txt(status, (x, 177), self.ui, self.ACC if 'move' in status.lower() else self.TEXT)
        self.txt(f'Eval {eval_cp / 100:+.2f}', (x, 207), self.ui)
        if label:
            pygame.draw.rect(self.screen, (52, 55, 60), (x, 235, 380, 42), border_radius=8)
            self.classification_badge(label, (x + 25, 256), 14)
            self.txt(label, (x + 48, 246), self.ui, self.LABEL_STYLE.get(label, ('?', self.ACC))[1])
        cap = self.captured(board)
        white_cap, black_cap = [], []
        for pt in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN):
            for _ in range(cap[chess.BLACK][pt]): white_cap.append(self.PIECES[pt])
            for _ in range(cap[chess.WHITE][pt]): black_cap.append(self.PIECES[pt])
        self.txt('CAPTURED', (x, 292), self.small, self.MUTED)
        self.txt(''.join(white_cap), (x, 310), self.ui, self.TEXT)
        self.txt(''.join(black_cap), (x, 333), self.ui, self.TEXT)
        self.txt('RECENT MOVES', (x, 363), self.small, self.MUTED)
        temp = chess.Board(); sans = []
        for move in board.move_stack:
            sans.append(temp.san(move)); temp.push(move)
        recent = sans[-7:]
        for i, san in enumerate(recent):
            self.txt(f'{len(sans) - len(recent) + i + 1:>2}. {san}', (x, 383 + i * 19), self.small)
        c = review.counts()
        self.txt(f'Accuracy {review.accuracy():.1f}%   Avg loss {review.average_loss():.0f}', (x, 520), self.small, self.ACC)
        self.txt(f'Best {c["BEST MOVE"]}  Great {c["GREAT MOVE"]}  Excellent {c["EXCELLENT MOVE"]}', (x, 542), self.small)
        self.txt(f'Inaccuracy {c["INACCURACY"]}  Mistake {c["MISTAKE"]}  Blunder {c["BLUNDER"]}', (x, 562), self.small)
        controls = ['B Bot  T Theme  C Clock  A Side', 'N New  U Undo  F Flip  H Hint', 'R Review  S Save PGN  P Pause', 'M Sound  Esc Quit']
        for i, line in enumerate(controls): self.txt(line, (x, 590 + i * 21), self.small)
        if paused: self.txt('PAUSED', (x + 310, 650), self.ui, self.RED)

    def _review_label(self, item):
        label = item.get('label', 'GOOD MOVE')
        icon, color = self.LABEL_STYLE.get(label, ('?', (150, 150, 150)))
        return label, icon, color

    def _review_board_for(self, item, after=False):
        fen = item.get('after_fen') if after else item.get('before_fen')
        if fen:
            try: return chess.Board(fen)
            except ValueError: pass
        return chess.Board()

    def _draw_graph(self, rows, rect):
        pygame.draw.rect(self.screen, (23, 24, 27), rect, border_radius=5)
        if not rows: return
        vals = []
        for item in rows:
            cp = float(item.get('played_cp', 0))
            vals.append(max(-1000, min(1000, cp)))
        pts = []
        for i, value in enumerate(vals):
            px = rect.x + 8 + (rect.w - 16) * (i / max(1, len(vals) - 1))
            py = rect.centery - (value / 1000) * (rect.h * 0.42)
            pts.append((px, py))
        pygame.draw.line(self.screen, (70, 72, 76), (rect.x + 5, rect.centery), (rect.right - 5, rect.centery), 1)
        if len(pts) > 1: pygame.draw.lines(self.screen, (120, 120, 120), False, pts, 2)
        for i, pt in enumerate(pts):
            label = rows[i].get('label', '')
            _, _, color = self._review_label(rows[i])
            pygame.draw.circle(self.screen, color, (int(pt[0]), int(pt[1])), 3)

    def show_review(self, review, engine):
        # A Chess.com-style review workspace: board left, dark move-review panel right,
        # classification icon on the current move, move list, graph and navigation.
        if not review.items:
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_r, pygame.K_RETURN)):
                        return
                self.screen.fill(self.PANELC)
                self.txt('GAME REVIEW', (35, 28), self.big, self.ACC)
                self.txt('Make a few moves first, then open Review again.', (35, 82), self.ui, self.MUTED)
                self.txt('Esc / R / Enter to close', (35, 650), self.small, self.MUTED)
                pygame.display.flip(); pygame.time.Clock().tick(60)

        index = len(review.items) - 1
        rows = review.items
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_r): return
                    if e.key in (pygame.K_LEFT, pygame.K_UP): index = max(0, index - 1)
                    elif e.key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_n): index = min(len(rows) - 1, index + 1)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mx, my = e.pos
                    if mx >= self.BOARD + 30 and 84 <= my <= 121:
                        index = min(len(rows) - 1, index + 1)
                    elif mx >= self.BOARD + 30 and my >= 650:
                        if mx < self.BOARD + 125: index = 0
                        elif mx < self.BOARD + 210: index = max(0, index - 1)
                        elif mx < self.BOARD + 350: index = min(len(rows) - 1, index + 1)
                        else: index = len(rows) - 1
                    elif mx >= self.BOARD + 28 and my >= 142 and my < 500:
                        clicked = (my - 142) // 22
                        if 0 <= clicked < len(rows): index = clicked

            item = rows[index]
            board = self._review_board_for(item, after=False)
            played = item.get('move')
            self.screen.fill(self.PANELC)
            self._draw_board(board, last=played, selected=False, coords=True, review_mode=True)
            self._draw_eval_bar(item.get('played_cp', 0))

            x = self.BOARD + 30
            pygame.draw.rect(self.screen, (31, 33, 36), (self.BOARD + 30, 0, 450, self.H))
            self.txt('‹', (x, 13), self.big, self.MUTED)
            self.txt('◉  GAME REVIEW', (x + 38, 20), self.small, self.TEXT)
            self.txt('⌕', (x + 405, 14), self.ui, self.MUTED)

            label, icon, color = self._review_label(item)
            banner = pygame.Rect(x, 52, 420, 58)
            pygame.draw.rect(self.screen, (246, 246, 246), banner, border_radius=8)
            self.classification_badge(label, (x + 28, 81), 16)
            try:
                temp = chess.Board(item.get('before_fen', chess.Board().fen()))
                san = temp.san(played) if played else '-'
            except Exception:
                san = played.uci() if played else '-'
            self.txt(f'{san} is the last {label.lower()}', (x + 53, 70), self.small, (35, 35, 35))
            self.txt(f'{item.get("played_cp", 0) / 100:+.2f}', (x + 365, 71), self.small, color)

            next_rect = pygame.Rect(x, 116, 420, 28)
            pygame.draw.rect(self.screen, (111, 174, 70), next_rect, border_radius=5)
            self.txt('Next  ›', (x + 187, 122), self.small, (255, 255, 255))

            # Move list with classification icons, like the supplied reference.
            list_top = 153
            row_h = 22
            visible_start = max(0, index - 15)
            visible = rows[visible_start:index + 1]
            for local_i, data in enumerate(visible):
                row_index = visible_start + local_i
                yy = list_top + local_i * row_h
                selected = row_index == index
                if selected:
                    pygame.draw.rect(self.screen, (45, 48, 52), (x, yy - 2, 420, row_h), border_radius=3)
                try:
                    b = chess.Board(data.get('before_fen', chess.Board().fen()))
                    san2 = b.san(data.get('move')) if data.get('move') else '-'
                except Exception:
                    san2 = data.get('move').uci() if data.get('move') else '-'
                self.txt(f'{row_index + 1:>2}.', (x + 8, yy), self.tiny, self.MUTED)
                self.txt(san2, (x + 38, yy), self.tiny, self.TEXT)
                self.classification_badge(data.get('label'), (x + 120, yy + 7), 9)
                best = data.get('best')
                self.txt(best.uci() if best else '-', (x + 145, yy), self.tiny, self.MUTED)
                rank = data.get('rank') or '-'
                self.txt(f'#{rank}', (x + 350, yy), self.tiny, self.MUTED)

            # Accuracy / classification summary
            cy = 505
            self.txt(f'Accuracy  {review.accuracy():.1f}%', (x, cy), self.ui, self.ACC)
            self.txt(f'Avg loss  {review.average_loss():.0f} cp', (x + 170, cy), self.small, self.MUTED)
            counts = review.counts()
            self.txt(f'Best {counts["BEST MOVE"]}   Great {counts["GREAT MOVE"]}   Excellent {counts["EXCELLENT MOVE"]}', (x, cy + 25), self.tiny, self.MUTED)
            self.txt(f'Inaccuracy {counts["INACCURACY"]}   Mistake {counts["MISTAKE"]}   Blunder {counts["BLUNDER"]}', (x, cy + 43), self.tiny, self.MUTED)

            self._draw_graph(rows, pygame.Rect(x, 575, 420, 62))
            nav_y = 650
            buttons = [('|‹', 0), ('‹', max(0, index - 1)), ('▶', min(len(rows) - 1, index + 1)), ('›|', len(rows) - 1)]
            for j, (symbol, target) in enumerate(buttons):
                rect = pygame.Rect(x + j * 106, nav_y, 96, 38)
                pygame.draw.rect(self.screen, (57, 59, 63), rect, border_radius=5)
                self.txt(symbol, (rect.centerx - 8, rect.y + 9), self.ui, self.TEXT)

            self.txt(f'Move {index + 1} / {len(rows)}', (35, 650), self.small, self.MUTED)
            pygame.display.flip()
            pygame.time.Clock().tick(60)
