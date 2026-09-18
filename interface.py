import pygame
import chess
import sys

# 1. Initialize Pygame Graphics Engine
pygame.init()
SQUARE_SIZE = 80
WINDOW_SIZE = 8 * SQUARE_SIZE
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Custom Stylized Chess Interface")
clock = pygame.time.Clock()

# 2. Extract Board Theme Palette from Your Image
LIGHT_SQUARE = (84, 84, 84)       # Medium Matte Dark Grey
DARK_SQUARE = (61, 61, 61)         # Deep Charcoal Grey
HIGHLIGHT_COLOR = (110, 110, 110)   # Highlight border color

# 3. Match the Solid-Filled Piece Profiles with Outlines from Your Image
# We use the solid filled characters '♚, ♛, ♜, ♝, ♞, ♟' for BOTH sides to get the solid shape!
SOLID_SYMBOLS = {
    'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

def draw_board(selected_square):
    """Draws the dark stylized checker pattern."""
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
    # Draw selected highlight box
    if selected_square is not None:
        col = chess.square_file(selected_square)
        row = 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)

def draw_pieces(board, font):
    """
    Renders the solid pieces with high-contrast outlines 
    matching your image perfectly by drawing multiple offset layers.
    """
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            
            # Use the solid symbol mapping
            char = SOLID_SYMBOLS[piece.symbol()]
            
            # Setup colors based on your image profiles
            if piece.color == chess.WHITE:
                fill_color = (255, 255, 255)   # Crisp Solid White
                border_color = (0, 0, 0)       # Bold Black Outline
            else:
                fill_color = (15, 15, 15)      # Deep Solid Black
                border_color = (230, 230, 230) # Crisp White Outline

            x_pos = col * SQUARE_SIZE + 12
            y_pos = row * SQUARE_SIZE + 5

            # Render 4-way offset cross-borders to simulate a bold outline stroke around the font vector
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                border_surf = font.render(char, True, border_color)
                screen.blit(border_surf, (x_pos + dx, y_pos + dy))
                
            # Render main solid interior profile right over the top
            main_surf = font.render(char, True, fill_color)
            screen.blit(main_surf, (x_pos, y_pos))

def main():
    board = chess.Board()
    # 'segoeuisymbol' handles these rich solid vector shapes beautifully
    piece_font = pygame.font.SysFont("segoeuisymbol", 54)
    selected_square = None
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over():
                pos = pygame.mouse.get_pos()
                col = pos[0] // SQUARE_SIZE
                row = 7 - (pos[1] // SQUARE_SIZE)
                clicked_square = chess.square(col, row)
                
                if selected_square is None:
                    piece = board.piece_at(clicked_square)
                    if piece and piece.color == board.turn:
                        selected_square = clicked_square
                else:
                    move = chess.Move(selected_square, clicked_square)
                    if board.piece_at(selected_square) and board.piece_at(selected_square).piece_type == chess.PAWN:
                        if chess.square_rank(clicked_square) in (0, 7):
                            move.promotion = chess.QUEEN
                            
                    if move in board.legal_moves:
                        board.push(move)
                    selected_square = None

        # Redraw Graphics Matrix Pipeline layout
        draw_board(selected_square)
        draw_pieces(board, piece_font)
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
