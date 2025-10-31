from __future__ import annotations

from typing import Iterator

from actions import (Action, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
                     SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, COMBINE, PAINT)
from block import Block

COMPUTER_ACTIONS: list[Action] = [
    ROTATE_CLOCKWISE,
    ROTATE_COUNTER_CLOCKWISE,
    SWAP_HORIZONTAL,
    SWAP_VERTICAL,
    SMASH,
    COMBINE,
    PAINT
]


def list_valid_moves(board: Block,
                     colour: tuple[int, int, int]) -> list[tuple[Action, tuple[int, ...]]]:
    """Return all valid non-pass moves available on <board>."""
    candidates: list[tuple[Action, tuple[int, ...]]] = []

    for block, path in _blocks_with_paths(board):
        for action in COMPUTER_ACTIONS:
            if not _is_potential_move(action, block, colour):
                continue

            board_copy = board.create_copy()
            target_copy = block_from_path(board_copy, path)
            if action.apply(target_copy, {'colour': colour}):
                candidates.append((action, path))

    return candidates


def block_from_path(block: Block, path: tuple[int, ...]) -> Block:
    """Return the block reached by following <path> from <block>."""
    current = block
    for index in path:
        current = current.children[index]
    return current


def _blocks_with_paths(block: Block) -> Iterator[tuple[Block, tuple[int, ...]]]:
    """Yield each block paired with its path from the root."""
    def helper(current: Block, path: tuple[int, ...]) -> Iterator[tuple[Block, tuple[int, ...]]]:
        yield current, path
        for index, child in enumerate(current.children):
            yield from helper(child, path + (index,))

    yield from helper(block, ())


def _is_potential_move(action: Action, block: Block,
                       colour: tuple[int, int, int]) -> bool:
    """Quick checks to skip obviously invalid actions."""
    if action in (ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
                  SWAP_HORIZONTAL, SWAP_VERTICAL):
        return len(block.children) != 0
    if action is SMASH:
        return block.smashable()
    if action is COMBINE:
        return len(block.children) != 0
    if action is PAINT:
        return (len(block.children) == 0 and block.level == block.max_depth
                and block.colour != colour)
    return True
