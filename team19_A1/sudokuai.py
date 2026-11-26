
import copy

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

    
    def apply_move(self, game_state: GameState, move: Move) -> GameState:
        """Create a new game state after a simulated move."""
        new_state = copy.deepcopy(game_state)
        player = new_state.current_player

        # Calculate points before filling the square.
        points = self._points_by_square(game_state.board)[move.square]

        # Update the board, score and move history.
        new_state.board.put(move.square, move.value)
        new_state.scores[player - 1] += points
        new_state.moves.append(move)

        # Update occupied squares.
        if player == 1:
            if new_state.occupied_squares1 is not None:
                new_state.occupied_squares1.append(move.square)
        else:
            if new_state.occupied_squares2 is not None:
                new_state.occupied_squares2.append(move.square)

        # Switch to the opponent.
        new_state.current_player = 3 - player

        return new_state

    def minimax(self, game_state: GameState, depth: int,
                alpha: float, beta: float, player: int) -> float:
        """Perform minimax search with alpha-beta pruning."""

        # Stop at the depth limit or a completed board.
        if depth == 0 or SudokuBoard.empty not in game_state.board.squares:
            return self.evaluate(game_state, player)

        moves = self.generate_legal_moves(game_state)

        # Handle positions with no candidate moves.
        if not moves:
            next_state = copy.copy(game_state)
            next_state.current_player = 3 - game_state.current_player

            if not self.generate_legal_moves(next_state):
                return self.evaluate(game_state, player)

            return self.minimax(
                next_state, depth - 1, alpha, beta, player
            )

        moves = self.order_moves(game_state, moves)

        # Maximizing player.
        if game_state.current_player == player:
            best_value = float("-inf")

            for move in moves:
                next_state = self.apply_move(game_state, move)

                value = self.minimax(
                    next_state, depth - 1, alpha, beta, player
                )

                best_value = max(best_value, value)
                alpha = max(alpha, best_value)

                if alpha >= beta:
                    break

            return best_value

        # Minimizing player.
        else:
            best_value = float("inf")

            for move in moves:
                next_state = self.apply_move(game_state, move)

                value = self.minimax(
                    next_state, depth - 1, alpha, beta, player
                )

                best_value = min(best_value, value)
                beta = min(beta, best_value)

                if alpha >= beta:
                    break

            return best_value

    def search_best_move(self, game_state: GameState, depth: int,
                         player: int) -> Move:
        """Find the best move at the specified search depth."""

        moves = self.generate_legal_moves(game_state)
        moves = self.order_moves(game_state, moves)

        best_move = moves[0]
        best_value = float("-inf")

        alpha = float("-inf")
        beta = float("inf")

        for move in moves:
            next_state = self.apply_move(game_state, move)

            value = self.minimax(
                next_state, depth - 1, alpha, beta, player
            )

            if value > best_value:
                best_value = value
                best_move = move

            alpha = max(alpha, best_value)

        return best_move

    def compute_best_move(self, game_state: GameState) -> None:
        """Use iterative deepening with alpha-beta minimax."""

        player = game_state.current_player
        moves = self.generate_legal_moves(game_state)

        if not moves:
            return

        # Immediately propose a legal fallback move.
        self.propose_move(moves[0])

        moves = self.order_moves(game_state, moves)
        self.propose_move(moves[0])

        # Iterative deepening.
        depth = 1
        max_depth = 2 * game_state.board.squares.count(SudokuBoard.empty)

        while depth <= max_depth:
            best_move = self.search_best_move(
                game_state, depth, player
            )

            self.propose_move(best_move)
            depth += 1

