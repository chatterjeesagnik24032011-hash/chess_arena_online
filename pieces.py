import pygame
import chess
import sys
import time

# 1. Initialize Pygame Graphics System
pygame.init()
SQUARE_SIZE = 80
WINDOW_SIZE = 8 * SQUARE_SIZE
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Chess vs Pro AI - Vector Graphics Mode")
clock = pygame.time.Clock()

# Elegant Slate & Cream Color Scheme
LIGHT_SQUARE = (245, 245, 220)  # Beige/Cream
DARK_SQUARE = (112, 128, 144)   # Slate Grey
HIGHLIGHT_COLOR = (143, 188, 143) # Soft Mint Green

PIECE_COLOR_WHITE = (255, 255, 255) # Pure White
PIECE_COLOR_BLACK = (20, 20, 20)    # Soft Charcoal

# High-Resolution Native Unicode Piece Characters
UNICODE_PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙', # White
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'  # Black
}

# Advanced Evaluation Arrays
PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}

PAWN_TABLE = [0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0]
KNIGHT_TABLE = [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30, -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30, -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50]
BISHOP_TABLE = [-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,10,10,5,0,-10, -10,5,5,10,10,5,5,-10, -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10, -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20]
ROOK_TABLE = [0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0]
QUEEN_TABLE = [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10, -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20]
KING_TABLE = [-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]

def draw_board(selected_square):
    """Draws chessboard checker tiles."""
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

def draw_pieces(board, font):
    """Draws pieces using native system typography vectors with subtle depth shadows."""
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            
            char = UNICODE_PIECES[piece.symbol()]
            main_color = PIECE_COLOR_WHITE if piece.color == chess.WHITE else PIECE_COLOR_BLACK
            
            # Layer 1: Draw dark ambient text occlusion drop shadow
            shadow_surface = font.render(char, True, (60, 60, 60, 100))
            screen.blit(shadow_surface, (col * SQUARE_SIZE + 13, row * SQUARE_SIZE + 7))
            
            # Layer 2: Draw the main crisp piece symbol over the top
            piece_surface = font.render(char, True, main_color)
            screen.blit(piece_surface, (col * SQUARE_SIZE + 12, row * SQUARE_SIZE + 5))

def evaluate_board(board):
    if board.is_checkmate(): return -99999 if board.turn == chess.WHITE else 99999
    if board.is_game_over(): return 0
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = PIECE_VALUES[piece.piece_type]
            sq_idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
            bonus = 0
            if piece.piece_type == chess.PAWN: bonus = PAWN_TABLE[sq_idx]
            elif piece.piece_type == chess.KNIGHT: bonus = KNIGHT_TABLE[sq_idx]
            elif piece.piece_type == chess.BISHOP: bonus = BISHOP_TABLE[sq_idx]
            elif piece.piece_type == chess.ROOK: bonus = ROOK_TABLE[sq_idx]
            elif piece.piece_type == chess.QUEEN: bonus = QUEEN_TABLE[sq_idx]
            elif piece.piece_type == chess.KING: bonus = KING_TABLE[sq_idx]
            
            total = value + bonus
            score += total if piece.color == chess.WHITE else -total
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over(): return evaluate_board(board), None
    legal_moves = list(board.legal_moves)
    legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)
    best_move = None

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if evaluation > max_eval: max_eval, best_move = evaluation, move
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if evaluation < min_eval: min_eval, best_move = evaluation, move
            beta = min(beta, evaluation)
            if beta <= alpha: break
        return min_eval, best_move

def make_advanced_ai_move(board, depth=3):
    start = time.time()
    _, best_move = minimax(board, depth, -float('inf'), float('inf'), False)
    elapsed = time.time() - start
    if elapsed < 0.4 and best_move: time.sleep(0.4 - elapsed)
    if best_move: board.push(best_move)

def display_game_status(board, font):
    if board.is_game_over():
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        msg = "Game Over!"
        if board.is_checkmate(): msg = "Checkmate! Pro Bot Wins!" if board.turn == chess.WHITE else "Checkmate! You Win!"
        elif board.is_stalemate(): msg = "Draw by Stalemate!"
        text_surface = font.render(msg, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        screen.blit(text_surface, text_rect)

def main():
    board = chess.Board()
    
    # Initialize fonts. "segoeuisymbol" or "arialunicodems" provide excellent vector symbols.
    piece_font = pygame.font.SysFont("segoeuisymbol", 54)
    ui_font = pygame.font.SysFont("Arial", 26, bold=True)
    
    selected_square = None
    HUMAN_TURN = chess.WHITE 
    
    running = True
    while running:
        # AI Turn Handler
        if not board.is_game_over() and board.turn != HUMAN_TURN:
            draw_board(selected_square)
            draw_pieces(board, piece_font)
            pygame.display.flip()
            make_advanced_ai_move(board, depth=3)

        # Human Input Handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over() and board.turn == HUMAN_TURN:
                pos = pygame.mouse.get_pos()
                
                # Fixed: Extract coordinates safely using tuple index markers before applying division
                col = pos[0] // SQUARE_SIZE
                row = 7 - (pos[1] // SQUARE_SIZE)
                clicked_square = chess.square(col, row)
                
                if selected_square is None:
                    piece = board.piece_at(clicked_square)
                    if piece and piece.color == HUMAN_TURN: selected_square = clicked_square
                else:
                    move = chess.Move(selected_square, clicked_square)
                    if board.piece_at(selected_square) and board.piece_at(selected_square).piece_type == chess.PAWN:
                        if chess.square_rank(clicked_square) in (0, 7): move.promotion = chess.QUEEN
                    
                    if move in board.legal_moves: board.push(move)
                    selected_square = None

        # Game Frame Redraw Stack
        draw_board(selected_square)
        draw_pieces(board, piece_font)
        display_game_status(board, ui_font)
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
