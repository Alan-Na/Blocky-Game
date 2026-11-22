"""Seeded property tests for Blocky boards.

Each test rebuilds a board from a fixed random seed and checks a property that
must hold for every board: the representation invariants, rotations and swaps
that undo each other, goal scores that stay within their bounds, and so on.
The seed and depth are part of the test name, so a failure can be reproduced
with ``_board(seed, depth)``.
"""
from __future__ import annotations

import random
from collections import Counter
from typing import Iterator

from block import Block, generate_board, ROT_CW, ROT_CCW, SWAP_HORZ, SWAP_VERT
from goal import BlobGoal, PerimeterGoal, flatten
from settings import BOARD_SIZE, COLOUR_LIST


def _board(seed: int, max_depth: int) -> Block:
    """Return the board generate_board builds after seeding random with <seed>.
    """
    random.seed(seed)
    return generate_board(max_depth, BOARD_SIZE)


def _blocks(block: Block) -> Iterator[Block]:
    """Yield <block> and all of its descendants, parents before children."""
    yield block
    for child in block.children:
        yield from _blocks(child)


def _leaves(block: Block) -> list[Block]:
    """Return every undivided block inside <block>."""
    return [b for b in _blocks(block) if not b.children]


def _colour_counts(block: Block) -> Counter:
    """Return how many unit cells of each colour <block> contains."""
    return Counter(cell for column in flatten(block) for cell in column)


def _check_invariants(block: Block) -> None:
    """Assert the Block representation invariants for <block> and all of its
    descendants.
    """
    assert 0 <= block.level <= block.max_depth
    assert len(block.children) in (0, 4)
    if block.children:
        assert block.colour is None
        positions = block.children_positions()
        for child, position in zip(block.children, positions):
            assert child.max_depth == block.max_depth
            assert child.level == block.level + 1
            assert child.size == block.child_size()
            assert child.position == position
            _check_invariants(child)
    else:
        assert block.colour in COLOUR_LIST


def test_double_swap_seed810097_depth3() -> None:
    """Swapping twice in the same direction leaves the board unchanged."""
    for direction in (SWAP_HORZ, SWAP_VERT):
        board = _board(810097, 3)
        original = board.create_copy()
        assert board.swap(direction)
        _check_invariants(board)
        assert board.swap(direction)
        assert board == original


def test_combine_majority_seed379940_depth3() -> None:
    """Combining keeps the most common child colour and refuses ties."""
    board = _board(379940, 3)
    parents = [b for b in _blocks(board)
               if b.children and all(not c.children for c in b.children)]
    assert parents
    for block in parents:
        counts = Counter(child.colour for child in block.children)
        top = max(counts.values())
        winners = [colour for colour, n in counts.items() if n == top]
        assert block.combine() == (len(winners) == 1)
        if len(winners) == 1:
            assert block.colour == winners[0]
            assert not block.children
    _check_invariants(board)


def test_rotation_cycle_seed452286_depth3() -> None:
    """Four clockwise rotations bring the board back to where it started."""
    board = _board(452286, 3)
    original = board.create_copy()
    for _ in range(4):
        assert board.rotate(ROT_CW)
    assert board == original
    _check_invariants(board)


def test_rotation_cycle_seed52940_depth3() -> None:
    """Four clockwise rotations bring the board back to where it started."""
    board = _board(52940, 3)
    original = board.create_copy()
    for _ in range(4):
        assert board.rotate(ROT_CW)
    assert board == original
    _check_invariants(board)


def test_combine_majority_seed726049_depth5() -> None:
    """Combining keeps the most common child colour and refuses ties."""
    board = _board(726049, 5)
    parents = [b for b in _blocks(board)
               if b.children and all(not c.children for c in b.children)]
    assert parents
    for block in parents:
        counts = Counter(child.colour for child in block.children)
        top = max(counts.values())
        winners = [colour for colour, n in counts.items() if n == top]
        assert block.combine() == (len(winners) == 1)
        if len(winners) == 1:
            assert block.colour == winners[0]
            assert not block.children
    _check_invariants(board)


def test_leaf_actions_seed870401_depth3() -> None:
    """Only max-depth leaves take paint; shallower leaves can still be smashed."""
    board = _board(870401, 3)
    for leaf in _leaves(board):
        other = next(c for c in COLOUR_LIST if c != leaf.colour)
        if leaf.level == 3:
            assert not leaf.smashable()
            assert not leaf.smash()
            assert leaf.paint(other)
            assert leaf.colour == other
            assert not leaf.paint(other)
        else:
            assert leaf.smashable()
            assert not leaf.paint(other)


def test_perimeter_total_seed476167_depth2() -> None:
    """Perimeter scores over the whole palette add up to the perimeter length."""
    board = _board(476167, 2)
    cells = 2 ** 2
    scores = [PerimeterGoal(colour).score(board) for colour in COLOUR_LIST]
    assert all(0 <= score <= 4 * cells for score in scores)
    assert sum(scores) == 4 * cells


def test_rotation_cycle_seed717715_depth2() -> None:
    """Four clockwise rotations bring the board back to where it started."""
    board = _board(717715, 2)
    original = board.create_copy()
    for _ in range(4):
        assert board.rotate(ROT_CW)
    assert board == original
    _check_invariants(board)


def test_colour_conservation_seed182301_depth3() -> None:
    """Swaps and rotations move cells around without changing colour counts."""
    board = _board(182301, 3)
    before = _colour_counts(board)
    assert board.swap(SWAP_HORZ)
    assert board.rotate(ROT_CW)
    assert board.swap(SWAP_VERT)
    assert board.rotate(ROT_CCW)
    assert _colour_counts(board) == before
    _check_invariants(board)


def test_rotation_undo_seed604759_depth4() -> None:
    """A counter-clockwise rotation undoes a clockwise one."""
    board = _board(604759, 4)
    original = board.create_copy()
    assert board.rotate(ROT_CW)
    _check_invariants(board)
    assert board.rotate(ROT_CCW)
    assert board == original


def test_flatten_shape_seed522639_depth2() -> None:
    """Flattening gives a square grid of palette colours, 2**depth wide."""
    grid = flatten(_board(522639, 2))
    cells = 2 ** 2
    assert len(grid) == cells
    for column in grid:
        assert len(column) == cells
        assert all(cell in COLOUR_LIST for cell in column)


def test_double_swap_seed476238_depth3() -> None:
    """Swapping twice in the same direction leaves the board unchanged."""
    for direction in (SWAP_HORZ, SWAP_VERT):
        board = _board(476238, 3)
        original = board.create_copy()
        assert board.swap(direction)
        _check_invariants(board)
        assert board.swap(direction)
        assert board == original


def test_flatten_shape_seed33777_depth2() -> None:
    """Flattening gives a square grid of palette colours, 2**depth wide."""
    grid = flatten(_board(33777, 2))
    cells = 2 ** 2
    assert len(grid) == cells
    for column in grid:
        assert len(column) == cells
        assert all(cell in COLOUR_LIST for cell in column)


def test_perimeter_total_seed494713_depth4() -> None:
    """Perimeter scores over the whole palette add up to the perimeter length."""
    board = _board(494713, 4)
    cells = 2 ** 4
    scores = [PerimeterGoal(colour).score(board) for colour in COLOUR_LIST]
    assert all(0 <= score <= 4 * cells for score in scores)
    assert sum(scores) == 4 * cells


def test_rotation_undo_seed218506_depth5() -> None:
    """A counter-clockwise rotation undoes a clockwise one."""
    board = _board(218506, 5)
    original = board.create_copy()
    assert board.rotate(ROT_CW)
    _check_invariants(board)
    assert board.rotate(ROT_CCW)
    assert board == original


def test_rotation_cycle_seed406755_depth3() -> None:
    """Four clockwise rotations bring the board back to where it started."""
    board = _board(406755, 3)
    original = board.create_copy()
    for _ in range(4):
        assert board.rotate(ROT_CW)
    assert board == original
    _check_invariants(board)


def test_flatten_shape_seed947782_depth2() -> None:
    """Flattening gives a square grid of palette colours, 2**depth wide."""
    grid = flatten(_board(947782, 2))
    cells = 2 ** 2
    assert len(grid) == cells
    for column in grid:
        assert len(column) == cells
        assert all(cell in COLOUR_LIST for cell in column)


def test_double_swap_seed319219_depth4() -> None:
    """Swapping twice in the same direction leaves the board unchanged."""
    for direction in (SWAP_HORZ, SWAP_VERT):
        board = _board(319219, 4)
        original = board.create_copy()
        assert board.swap(direction)
        _check_invariants(board)
        assert board.swap(direction)
        assert board == original


def test_copy_independence_seed444103_depth4() -> None:
    """A copy equals the board but shares none of its blocks."""
    board = _board(444103, 4)
    duplicate = board.create_copy()
    assert duplicate == board
    assert not ({id(b) for b in _blocks(board)}
                & {id(b) for b in _blocks(duplicate)})
    duplicate.rotate(ROT_CW)
    duplicate.swap(SWAP_HORZ)
    assert board == _board(444103, 4)


def test_combine_majority_seed348543_depth3() -> None:
    """Combining keeps the most common child colour and refuses ties."""
    board = _board(348543, 3)
    parents = [b for b in _blocks(board)
               if b.children and all(not c.children for c in b.children)]
    assert parents
    for block in parents:
        counts = Counter(child.colour for child in block.children)
        top = max(counts.values())
        winners = [colour for colour, n in counts.items() if n == top]
        assert block.combine() == (len(winners) == 1)
        if len(winners) == 1:
            assert block.colour == winners[0]
            assert not block.children
    _check_invariants(board)


def test_rotation_undo_seed710832_depth3() -> None:
    """A counter-clockwise rotation undoes a clockwise one."""
    board = _board(710832, 3)
    original = board.create_copy()
    assert board.rotate(ROT_CW)
    _check_invariants(board)
    assert board.rotate(ROT_CCW)
    assert board == original
