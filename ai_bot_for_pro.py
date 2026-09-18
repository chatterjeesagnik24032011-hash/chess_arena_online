import pygame
import chess
import sys
import time

# 1. Initialize Pygame Graphics
pygame.init()
SQUARE_SIZE = 80
WINDOW_SIZE = 8 * SQUARE_SIZE
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Chess vs Advanced Minimax AI (Depth 3/4)")
clock = pygame.time.Clock()

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (130, 151, 105)

# Standard piece values for evaluation
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Positional tables to encourage center control, development, and tactical sacrifices (Brilliant moves)
# We view the board from White's perspective, so we reverse it for Black (the AI)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

def draw_board(selected_square):
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

# Solid chess-piece glyphs, matching the bold graphic/vector appearance
SOLID_SYMBOLS = {
    'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}


def draw_pieces(board, piece_font):
    """
    Draws large solid chess-piece glyphs with a contrasting outline.
    White pieces: white fill + black outline.
    Black pieces: black fill + white outline.
    """
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)

            char = SOLID_SYMBOLS[piece.symbol()]

            if piece.color == chess.WHITE:
                fill_color = (255, 255, 255)
                border_color = (0, 0, 0)
            else:
                fill_color = (15, 15, 15)
                border_color = (230, 230, 230)

            x_pos = col * SQUARE_SIZE + 12
            y_pos = row * SQUARE_SIZE + 5

            # Thick graphic-style outline
            for dx, dy in [
                (-2, 0), (2, 0), (0, -2), (0, 2),
                (-1, -1), (1, 1), (-1, 1), (1, -1)
            ]:
                border_surf = piece_font.render(char, True, border_color)
                screen.blit(border_surf, (x_pos + dx, y_pos + dy))

            # Solid interior
            main_surf = piece_font.render(char, True, fill_color)
            screen.blit(main_surf, (x_pos, y_pos))

def evaluate_board(board):
    """Advanced evaluation with Material + Positional Tables to reward smart/brilliant moves."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_game_over():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # Base piece score
            value = PIECE_VALUES[piece.piece_type]
            
            # Positional lookup index (0 to 63)
            sq_idx = square
            if piece.color == chess.BLACK:
                # Black pieces look at the board flipped upside down
                sq_idx = chess.square_mirror(square)
            
            # Extract position bonus based on type
            p_type = piece.piece_type
            bonus = 0
            if p_type == chess.PAWN: bonus = PAWN_TABLE[sq_idx]
            elif p_type == chess.KNIGHT: bonus = KNIGHT_TABLE[sq_idx]
            elif p_type == chess.BISHOP: bonus = BISHOP_TABLE[sq_idx]
            elif p_type == chess.ROOK: bonus = ROOK_TABLE[sq_idx]
            elif p_type == chess.QUEEN: bonus = QUEEN_TABLE[sq_idx]
            elif p_type == chess.KING: bonus = KING_TABLE[sq_idx]

            total_val = value + bonus
            if piece.color == chess.WHITE:
                score += total_val
            else:
                score -= total_val
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax core calculation with rapid Alpha-Beta Pruning branches pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    legal_moves = list(board.legal_moves)
    # Move ordering optimization: prioritize captures/checks to speed up alpha-beta pruning
    legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

    best_move = None

    if maximizing_player:  # White's Turn (Maximize score)
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval, best_move

    else:  # AI / Black's Turn (Minimize score)
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval, best_move

def make_advanced_ai_move(board, depth=3):
    """Triggers the lookahead tree sequence."""
    start_time = time.time()
    
    # AI plays as Black, so maximizing_player = False
    _, best_move = minimax(board, depth, -float('inf'), float('inf'), False)
    
    # Enforce a small humanized floor pause if calculation was near-instant
    elapsed = time.time() - start_time
    if elapsed < 0.4 and best_move:
        time.sleep(0.4 - elapsed)
        
    if best_move:
        board.push(best_move)

def display_game_status(board, ui_font):
    if board.is_game_over():
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        status_msg = "Game Over!"
        if board.is_checkmate():
            status_msg = "Checkmate! AI Wins!" if board.turn == chess.WHITE else "Checkmate! You Win!"
        elif board.is_stalemate():
            status_msg = "Draw by Stalemate!"
        text_surface = ui_font.render(status_msg, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        screen.blit(text_surface, text_rect)

def main():
    board = chess.Board()
    piece_font = pygame.font.SysFont(["segoeuisymbol", "dejavusans", "arial"], 54)
    ui_font = pygame.font.SysFont("Arial", 26, bold=True)
    selected_square = None
    HUMAN_TURN = chess.WHITE 
    
    running = True
    while running:
        # AI Turn Handling
        if not board.is_game_over() and board.turn != HUMAN_TURN:
            draw_board(selected_square)
            draw_pieces(board, piece_font)
            pygame.display.flip()
            
            make_advanced_ai_move(board, depth=3)

        # Human Input Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over() and board.turn == HUMAN_TURN:
                pos = pygame.mouse.get_pos()
                
                # FIXED: Extracted tuple values securely before division operations
                col = pos[0] // SQUARE_SIZE
                row = 7 - (pos[1] // SQUARE_SIZE)
                clicked_square = chess.square(col, row)
                
                if selected_square is None:
                    piece = board.piece_at(clicked_square)
                    if piece and piece.color == HUMAN_TURN:
                        selected_square = clicked_square
                else:
                    move = chess.Move(selected_square, clicked_square)
                    if board.piece_at(selected_square) and board.piece_at(selected_square).piece_type == chess.PAWN:
                        if chess.square_rank(clicked_square) in (0, 7):
                            move.promotion = chess.QUEEN
                    
                    if move in board.legal_moves:
                        board.push(move)
                        
                    selected_square = None

        # Render Loop
        draw_board(selected_square)
        draw_pieces(board, piece_font)
        display_game_status(board, ui_font)
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
