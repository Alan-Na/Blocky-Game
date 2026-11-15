"""Checks that every puzzle in puzzles/catalog.py is well formed and
reproducible.
"""
from __future__ import annotations

import random

from puzzles import GOAL_TYPES, all_puzzles, get_puzzle
from settings import COLOUR_LIST, colour_name


def test_numbers_are_unique_and_increasing() -> None:
    numbers = [puzzle.number for puzzle in all_puzzles()]
    assert numbers == sorted(set(numbers))


def test_names_and_seeds_are_unique() -> None:
    puzzles = all_puzzles()
    assert len({puzzle.name for puzzle in puzzles}) == len(puzzles)
    assert len({puzzle.seed for puzzle in puzzles}) == len(puzzles)


def test_fields_are_valid() -> None:
    colour_names = {colour_name(colour) for colour in COLOUR_LIST}
    for puzzle in all_puzzles():
        assert puzzle.goal in GOAL_TYPES
        assert puzzle.colour in colour_names
        assert 2 <= puzzle.max_depth <= 5
        assert puzzle.moves >= 1


def test_boards_are_reproducible() -> None:
    for puzzle in all_puzzles():
        assert puzzle.build_board() == puzzle.build_board()


def test_build_board_keeps_global_random_state() -> None:
    random.seed(148)
    expected = random.random()
    random.seed(148)
    for puzzle in all_puzzles():
        puzzle.build_board()
    assert random.random() == expected


def test_start_score_leaves_room_to_improve() -> None:
    for puzzle in all_puzzles():
        board = puzzle.build_board()
        assert 0 <= puzzle.start_score(board) < puzzle.max_score()


def test_get_puzzle_finds_every_number() -> None:
    for puzzle in all_puzzles():
        assert get_puzzle(puzzle.number) == puzzle
