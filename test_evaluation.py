import unittest

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
from team19_A1.sudokuai import SudokuAI


def make_board(holes=(), m=2, n=2):
    board = SudokuBoard(m, n)
    for row in range(board.N):
        for column in range(board.N):
            square = (row, column)
            if square not in holes:
                value = (row * n + row // m + column) % board.N + 1
                board.put(square, value)
    return board


class TestEvaluation(unittest.TestCase):
    def setUp(self):
        self.ai = SudokuAI()

    def test_region_completion_points(self):
        cases = [
            (0, {(0, 0), (0, 1), (1, 0)}),
            (1, {(0, 0), (0, 1)}),
            (3, {(0, 0), (0, 2)}),
            (7, {(0, 0)}),
        ]
        for expected, holes in cases:
            with self.subTest(expected=expected):
                board = make_board(holes)
                self.assertEqual(self.ai._points_by_square(board)[(0, 0)], expected)

    def test_rectangular_block_completion(self):
        for m, n in ((2, 3), (3, 2)):
            with self.subTest(m=m, n=n):
                target = (m, n)
                holes = {target, (m, 0), (0, n)}
                board = make_board(holes, m=m, n=n)
                self.assertEqual(self.ai._points_by_square(board)[target], 1)

    def test_evaluation_uses_fixed_player_perspective(self):
        state = GameState(board=make_board({(0, 0)}), scores=[5, 2],
                          current_player=2)
        self.assertEqual(self.ai.evaluate(state, 1), 3 - 0.25 * 7)
        self.assertEqual(self.ai.evaluate(state, 2), -3 + 0.25 * 7)

    def test_opportunity_requires_access_and_non_taboo_move(self):
        board = make_board({(0, 0)})
        blocked = GameState(board=board, scores=[5, 2], allowed_squares1=[(3, 3)],
                            occupied_squares1=[])
        taboo = GameState(board=board, scores=[5, 2], taboo_moves=[TabooMove((0, 0), 1)])
        for state in (blocked, taboo):
            self.assertEqual(self.ai.evaluate(state, 1), 3)

    def test_full_board_evaluates_to_score_difference(self):
        state = GameState(board=make_board(), scores=[4, 9])
        self.assertEqual(self.ai.evaluate(state, 1), -5)

    def test_order_moves_prioritizes_points_and_keeps_all_candidates(self):
        board = make_board({(0, 0), (2, 2), (2, 3), (3, 2), (3, 3)})
        state = GameState(board=board)
        scoring = Move((0, 0), 1)
        candidates = list(reversed(self.ai.generate_legal_moves(state)))
        original_order = candidates.copy()
        before = board.squares.copy()
        ordered = self.ai.order_moves(state, candidates)
        self.assertEqual(ordered[0], scoring)
        expected_rest = sorted((move.square, move.value) for move in candidates
                               if move.square != scoring.square)
        self.assertEqual([(move.square, move.value) for move in ordered[1:]], expected_rest)
        self.assertEqual(candidates, original_order)
        self.assertEqual(board.squares, before)
        self.assertEqual(self.ai.order_moves(state, []), [])
