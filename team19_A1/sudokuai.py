
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
        if allowed_cells is None:
            allowed_cells = ((i, j) for i in range(N) for j in range(N))

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

    def _points_by_square(self, board: SudokuBoard) -> dict[tuple[int, int], int]:
        """Map each empty square to the points earned by filling it."""
        row_empty = [0] * board.N
        column_empty = [0] * board.N
        block_empty = [0] * board.N
        empty_squares = []

        for row in range(board.N):
            for column in range(board.N):
                if board.get((row, column)) == SudokuBoard.empty:
                    block = (row // board.m) * board.m + column // board.n
                    empty_squares.append((row, column, block))
                    row_empty[row] += 1
                    column_empty[column] += 1
                    block_empty[block] += 1

        points = {}
        for row, column, block in empty_squares:
            regions_completed = sum((row_empty[row] == 1,
                                     column_empty[column] == 1,
                                     block_empty[block] == 1))
            points[row, column] = (0, 1, 3, 7)[regions_completed]
        return points

    def evaluate(self, game_state: GameState, player: int) -> float:
        """Evaluate a position from a fixed player's perspective (1 or 2)."""
        score_difference = game_state.scores[player - 1] - game_state.scores[2 - player]
        points = self._points_by_square(game_state.board)
        if not any(points.values()):
            return score_difference

        best_available_points = max(
            (points[move.square] for move in self.generate_legal_moves(game_state)),
            default=0,
        )
        # Discount potential points because the oracle can still reject the move.
        opportunity = 0.25 * best_available_points
        if game_state.current_player == player:
            return score_difference + opportunity
        return score_difference - opportunity

    def order_moves(self, game_state: GameState, moves: list[Move]) -> list[Move]:
        """Return the current player's highest-scoring moves first."""
        if not moves:
            return []
        points = self._points_by_square(game_state.board)
        return sorted(moves, key=lambda move: (-points[move.square], move.square, move.value))

    def compute_best_move(self, game_state: GameState) -> None:

        moves = self.generate_legal_moves(game_state)

        if moves:
            self.propose_move(random.choice(moves))
