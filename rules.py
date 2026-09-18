import chess

class ChessRulesEngine:
    def __init__(self):
        """Initializes a new chess game state using the python-chess core backend."""
        self.board = chess.Board()

    def get_piece_at_square(self, row, col):
        """
        Translates a Pygame grid click (row, col) into a chess piece symbol.
        Returns strings like 'wP' (White Pawn), 'bK' (Black King), or None.
        """
        square = self._coords_to_square(row, col)
        piece = self.board.piece_at(square)
        
        if piece is None:
            return None
            
        color_prefix = 'w' if piece.color == chess.WHITE else 'b'
        piece_symbol = piece.symbol().upper()
        return color_prefix + piece_symbol

    def get_legal_moves_for_piece(self, row, col):
        """Returns a list of destination squares (row, col) where a piece can legally move."""
        start_square = self._coords_to_square(row, col)
        legal_destinations = []
        
        for move in self.board.legal_moves:
            if move.from_square == start_square:
                # Convert the legal target square index back to 2D screen coordinates
                dest_col = chess.square_file(move.to_square)
                dest_row = 7 - chess.square_rank(move.to_square)
                legal_destinations.append((dest_row, dest_col))
                
        return legal_destinations

    def attempt_move(self, start_coords, end_coords):
        """
        Verifies if a move from start to end is legal.
        If legal, it executes the move on the board and switches turns.
        Returns True if successful, False otherwise.
        """
        start_square = self._coords_to_square(start_coords[0], start_coords[1])
        end_square = self._coords_to_square(end_coords[0], end_coords[1])
        
        # Formulate a basic standard chess move
        move = chess.Move(start_square, end_square)
        
        # Lookahead rule: If a pawn hits the edge ranks, automatically promote to a Queen
        piece = self.board.piece_at(start_square)
        if piece and piece.piece_type == chess.PAWN:
            end_rank = chess.square_rank(end_square)
            if end_rank == 0 or end_rank == 7:
                move.promotion = chess.QUEEN

        # Validate against strict official rules engine parameters
        if move in self.board.legal_moves:
            self.board.push(move)  # Execute move permanently changing engine state
            return True
            
        return False

    def is_current_turn_white(self):
        """Returns True if it is White's turn to move."""
        return self.board.turn == chess.WHITE

    def check_game_status(self):
        """
        Evaluates if the game has ended.
        Returns a dictionary containing game status strings.
        """
        if not self.board.is_game_over():
            return {"over": False, "result": "Active"}
            
        if self.board.is_checkmate():
            # If game is over and it's White's turn, Black delivered the mate
            winner = "Black Wins" if self.board.turn == chess.WHITE else "White Wins"
            return {"over": True, "result": f"Checkmate! {winner}"}
            
        if self.board.is_stalemate():
            return {"over": True, "result": "Draw by Stalemate!"}
            
        if self.board.is_insufficient_material():
            return {"over": True, "result": "Draw by Insufficient Material!"}
            
        return {"over": True, "result": "Draw!"}

    def _coords_to_square(self, row, col):
        """Helper to convert 2D Pygame matrix indices into python-chess 0-63 grid references."""
        file_idx = col
        rank_idx = 7 - row  # Flips index because chess ranks count upwards from the bottom
        return chess.square(file_idx, rank_idx)
