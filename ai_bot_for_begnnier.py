import pygame
import chess
import random
import sys
import time

# ==============================================================================
# 1. INITIALIZE GRAPHICS ENGINE CANVAS
# ==============================================================================
pygame.init()
SQUARE_SIZE = 80
WINDOW_SIZE = 8 * SQUARE_SIZE
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Chess vs Beginner AI Bot (Graphical Vector Mode)")
clock = pygame.time.Clock()

# ==============================================================================
# 2. DESIGN THEME PALETTE FROM THE INTERFACE IMAGE
# ==============================================================================
LIGHT_SQUARE = (84, 84, 84)       # Medium Matte Dark Grey
DARK_SQUARE = (61, 61, 61)         # Deep Charcoal Grey
HIGHLIGHT_COLOR = (110, 110, 110)   # Highlight border color

# Force solid glyph maps for BOTH sides to create the solid graphic look
SOLID_SYMBOLS = {
    'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

# ==============================================================================
# 3. GRAPHICS PIPELINE RENDERING METHODS
# ==============================================================================
def draw_board(selected_square):
    """Draws the dark stylized checker pattern."""
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
    # Draw selected green highlight border square box
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)

def draw_pieces(board, font):
    """
    Renders solid vector pieces with high-contrast bold outlines 
    matching your layout image seamlessly by drawing multi-shifted text passes.
    """
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            
            # Map the piece symbol to the solid shape character
            char = SOLID_SYMBOLS[piece.symbol()]
            
            # Setup fill and stroke parameters matching image profiles
            if piece.color == chess.WHITE:
                fill_color = (255, 255, 255)   # Solid White Fill
                border_color = (0, 0, 0)       # Bold Black Outline
            else:
                fill_color = (15, 15, 15)      # Deep Black Fill
                border_color = (230, 230, 230) # Crisp White Outline

            x_pos = col * SQUARE_SIZE + 12
            y_pos = row * SQUARE_SIZE + 5

            # Multi-directional shadow offset stamps create the thick graphic outline stroke look
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                border_surf = font.render(char, True, border_color)
                screen.blit(border_surf, (x_pos + dx, y_pos + dy))
                
            # Render main solid interior profile right over the top
            main_surf = font.render(char, True, fill_color)
            screen.blit(main_surf, (x_pos, y_pos))

# ==============================================================================
# 4. BOT GAMEPLAY LOGIC & STATUS ANNOUNCEMENTS
# ==============================================================================
def make_ai_move(board):
    """Beginner Bot: Grabs all legal moves and chooses one completely at random."""
    legal_moves = list(board.legal_moves)
    if legal_moves:
        # Pause briefly (half a second) so the AI move sequence feels natural
        time.sleep(0.5) 
        chosen_move = random.choice(legal_moves)
        board.push(chosen_move)

def display_game_status(board, font):
    """Overlays game over announcements on screen if checkmate or draw happens."""
    if board.is_game_over():
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent dark overlay mask
        screen.blit(overlay, (0, 0))
        
        status_msg = "Game Over!"
        if board.is_checkmate():
            status_msg = "Checkmate! AI Wins!" if board.turn == chess.WHITE else "Checkmate! You Win!"
        elif board.is_stalemate():
            status_msg = "Draw by Stalemate!"
            
        text_surface = font.render(status_msg, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        screen.blit(text_surface, text_rect)

# ==============================================================================
# 5. CORE CONTROLLER INTERACTION INITIALIZER
# ==============================================================================
def main():
    board = chess.Board()
    
    # Fonts: "segoeuisymbol" handles these rich solid glyph vectors perfectly
    piece_font = pygame.font.SysFont("segoeuisymbol", 54)
    ui_font = pygame.font.SysFont("Arial", 26, bold=True)
    
    selected_square = None
    HUMAN_TURN = chess.WHITE 
    
    running = True
    while running:
        # Check if it is the AI Bot's turn to act
        if not board.is_game_over() and board.turn != HUMAN_TURN:
            # Refresh screen elements so human registers their move before AI thinks
            draw_board(selected_square)
            draw_pieces(board, piece_font)
            pygame.display.flip()
            
            make_ai_move(board)

        # Handle Interaction Input Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over() and board.turn == HUMAN_TURN:
                pos = pygame.mouse.get_pos()
                
                # Clean mathematical coordinate tuple extraction tracking
                col = pos[0] // SQUARE_SIZE
                row = 7 - (pos[1] // SQUARE_SIZE)
                clicked_square = chess.square(col, row)
                
                if selected_square is None:
                    # Select human's own white pieces
                    piece = board.piece_at(clicked_square)
                    if piece and piece.color == HUMAN_TURN:
                        selected_square = clicked_square
                else:
                    move = chess.Move(selected_square, clicked_square)
                    
                    # Manage auto pawn-to-queen promotion on edge ranks
                    if board.piece_at(selected_square) and board.piece_at(selected_square).piece_type == chess.PAWN:
                        if chess.square_rank(clicked_square) in (0, 7):
                            move.promotion = chess.QUEEN
                    
                    # Execute move if validated by engine rules
                    if move in board.legal_moves:
                        board.push(move)
                        
                    selected_square = None  # Clear selector matrix box flag

        # Refreshes graphic frames sequentially 30 times a second
        draw_board(selected_square)
        draw_pieces(board, piece_font)
        display_game_status(board, ui_font)
        
        pygame.display.flip()
        clock.tick(30)

    # Clean window termination closure sequence
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
