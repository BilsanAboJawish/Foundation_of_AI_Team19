
import random

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):

    def __init__(self):
        super().__init__()

    def generate_legal_moves(self, game_state: GameState):
        board = game_state.board
        N = board.N
        m = board.m
        n = board.n

        legal_moves = []

        # Cells accessible to the current player
        allowed_cells = game_state.player_squares()

        for i, j in allowed_cells:

            # 1. The cell must be empty
            if board.get((i, j)) != SudokuBoard.empty:
                continue

            # 2. Find numbers already used in the row
            row_values = {
                board.get((i, col))
                for col in range(N)
            }

            # 3. Find numbers already used in the column
            col_values = {
                board.get((row, j))
                for row in range(N)
            }

            # 4. Find numbers already used in the block
            start_row = (i // m) * m
            start_col = (j // n) * n

            block_values = {
                board.get((row, col))
                for row in range(start_row, start_row + m)
                for col in range(start_col, start_col + n)
            }

            used_values = row_values | col_values | block_values

            # 5. Try every possible number
            for value in range(1, N + 1):

                # Respect Sudoku uniqueness rules
                if value in used_values:
                    continue

                # Respect taboo restrictions
                if TabooMove((i, j), value) in game_state.taboo_moves:
                    continue

                # This move satisfies all immediate rules
                legal_moves.append(Move((i, j), value))

        return legal_moves

    def compute_best_move(self, game_state: GameState) -> None:

        moves = self.generate_legal_moves(game_state)

        if moves:
            self.propose_move(random.choice(moves))
