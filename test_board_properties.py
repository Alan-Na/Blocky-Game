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
