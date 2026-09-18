import pygame
import chess
import sys

# 1. Initialize Pygame Graphics System
pygame.init()

# 2. Configure Dimensions
BOARD_SIZE = 8
SQUARE_SIZE = 80  # Size of each cell in pixels
WINDOW_SIZE = BOARD_SIZE * SQUARE_SIZE

# 3. Colors (Classic wooden chess board aesthetics)
LIGHT_SQUARE = (240, 217, 181)  # Cream
DARK_SQUARE = (181, 136, 99)    # Brown

# Set up the display canvas
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Chess Board Layout")

def draw_grid():
    """Draws an 8x8 chessboard pattern."""
    for file_idx in range(BOARD_SIZE):       # Columns (a to h)
        for rank_idx in range(BOARD_SIZE):   # Rows (1 to 8)
            
            # Alternating math pattern: if sum of indices is even -> Light square
            if (file_idx + rank_idx) % 2 == 0:
                color = LIGHT_SQUARE
            else:
                color = DARK_SQUARE
                
            # Pygame draws from the top-left down. 
            # We use rank_idx directly to fill the grid row-by-row on the screen.
            square_rect = pygame.Rect(
                file_idx * SQUARE_SIZE, 
                rank_idx * SQUARE_SIZE, 
                SQUARE_SIZE, 
                SQUARE_SIZE
            )
            pygame.draw.rect(screen, color, square_rect)

def main():
    # Use python-chess just to initialize a core board context structure
    board = chess.Board()
    clock = pygame.time.Clock()

    running = True
    while running:
        # Event Loop (Allows you to move or close the window cleanly)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Step 1: Render the board squares on screen
        draw_grid()

        # Step 2: Refresh display buffer
        pygame.display.flip()
        
        # Frame rate limit (30 FPS keeps CPU usage minimal)
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
