"""Tests for team19_A1.SudokuAI.generate_legal_moves.

Place this file next to simulate_game.py (the project root), then run:
    python3 -m unittest -v test_legal_moves

No changes to the provided competitive_sudoku framework are required.
"""
import unittest
from team19_A1.sudokuai import SudokuAI
from competitive_sudoku.sudoku import TabooMove


class FakeBoard:
    """Minimal board interface used by the team's move generator."""

    def __init__(self, m, n, rows=None):
        self.m, self.n, self.N = m, n, m * n
        self.rows = rows if rows is not None else [
            [0] * self.N for _ in range(self.N)
        ]

    def get(self, square):
        r, c = square
        return self.rows[r][c]


class FakeGameState:
    """Only implements fields/methods read by generate_legal_moves."""

    def __init__(self, board, allowed, taboo=()):
        self.board = board
        self._allowed = allowed
        self.taboo_moves = list(taboo)

    def player_squares(self):
        return self._allowed


def unpack(move):
    """Convert the framework's Move object to (row, column, number)."""
    if hasattr(move, 'square'):
        return (*move.square, move.value)
    return (move.i, move.j, move.value)


class TestLegalMoves(unittest.TestCase):
    def setUp(self):
        self.ai = SudokuAI()

    def moves(self, state):
        result = [unpack(move) for move in self.ai.generate_legal_moves(state)]
        self.assertEqual(len(result), len(set(result)), 'Duplicate moves found')
        return set(result)

    def test_empty_4x4_allowed_one_cell(self):
        s = FakeGameState(FakeBoard(2, 2), {(0, 0)})
        self.assertEqual(self.moves(s), {(0, 0, v) for v in (1, 2, 3, 4)})

    def test_allowed_cells_only(self):
        s = FakeGameState(FakeBoard(2, 2), {(0, 1)})
        self.assertEqual(self.moves(s), {(0, 1, v) for v in (1, 2, 3, 4)})

    def test_occupied_cells_excluded(self):
        b = FakeBoard(2, 2)
        b.rows[0][0] = 1
        s = FakeGameState(b, {(0, 0)})
        self.assertEqual(self.moves(s), set())

    def test_row_conflict(self):
        b = FakeBoard(2, 2)
        b.rows[0][3] = 1
        s = FakeGameState(b, {(0, 0)})
        self.assertEqual(self.moves(s), {(0, 0, v) for v in (2, 3, 4)})

    def test_column_conflict(self):
        b = FakeBoard(2, 2)
        b.rows[3][0] = 2
        s = FakeGameState(b, {(0, 0)})
        self.assertEqual(self.moves(s), {(0, 0, v) for v in (1, 3, 4)})

    def test_block_conflict(self):
        b = FakeBoard(2, 2)
        b.rows[1][1] = 3
        s = FakeGameState(b, {(0, 0)})
        self.assertEqual(self.moves(s), {(0, 0, v) for v in (1, 2, 4)})

    def test_combined_conflicts(self):
        b = FakeBoard(2, 2)
        b.rows[0][3] = 1  # same row
        b.rows[3][0] = 2  # same column
        b.rows[1][1] = 3  # same block
        s = FakeGameState(b, {(0, 0)})
        self.assertEqual(self.moves(s), {(0, 0, 4)})

    def test_taboo_move_excluded_not_whole_cell(self):
        s = FakeGameState(FakeBoard(2, 2), {(0, 0)},
                          [TabooMove((0, 0), 3)])
        self.assertEqual(self.moves(s), {(0, 0, v) for v in (1, 2, 4)})

    def test_different_cell_taboo_does_not_block(self):
        s = FakeGameState(FakeBoard(2, 2), {(0, 0)},
                          [TabooMove((0, 1), 3)])
        self.assertEqual(self.moves(s), {(0, 0, v) for v in (1, 2, 3, 4)})

    def test_no_allowed_cells(self):
        self.assertEqual(self.moves(FakeGameState(FakeBoard(2, 2), set())), set())

    def test_all_moves_taboo(self):
        taboo = [TabooMove((0, 0), v) for v in range(1, 5)]
        s = FakeGameState(FakeBoard(2, 2), {(0, 0)}, taboo)
        self.assertEqual(self.moves(s), set())

    def test_rectangular_2_by_3_blocks(self):
        b = FakeBoard(2, 3)
        b.rows[0][2] = 5  # same block as (1,0)
        b.rows[0][3] = 6  # different block, row and column
        b.rows[2][1] = 4  # different row block, row and column
        b.rows[0][0] = 2  # same column as (1,0)
        b.rows[1][4] = 3  # same row as (1,0)
        s = FakeGameState(b, {(1, 0)})
        self.assertEqual(self.moves(s), {(1, 0, v) for v in (1, 4, 6)})

    def test_rectangular_3_by_2_blocks(self):
        b = FakeBoard(3, 2)
        b.rows[0][0] = 5  # same block as (2,1)
        b.rows[3][0] = 6  # different block, row and column
        b.rows[0][2] = 4  # different block, row and column
        s = FakeGameState(b, {(2, 1)})
        self.assertEqual(self.moves(s), {(2, 1, v) for v in (1, 2, 3, 4, 6)})

    def test_9x9_produces_nine_values(self):
        s = FakeGameState(FakeBoard(3, 3), {(8, 8)})
        self.assertEqual(self.moves(s), {(8, 8, v) for v in range(1, 10)})

    def test_all_allowed_cells_considered(self):
        s = FakeGameState(FakeBoard(2, 2), {(0, 0), (0, 1)})
        self.assertEqual(self.moves(s), {
            (r, c, v) for r, c in [(0, 0), (0, 1)] for v in range(1, 5)
        })

    def test_generator_does_not_change_board(self):
        b = FakeBoard(2, 2)
        b.rows[2][3] = 4
        before = [row[:] for row in b.rows]
        s = FakeGameState(b, {(0, 0)})
        self.moves(s)
        self.assertEqual(b.rows, before)


if __name__ == '__main__':
    unittest.main()
