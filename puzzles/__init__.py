"""Seeded Blocky puzzles.

A puzzle pins down everything random about a starting position: the seed used
to generate the board, the board depth, the goal and its target colour, and
how many moves the player gets. Loading the same puzzle always produces the
same board, so puzzles can be shared and replayed.

Run ``python -m puzzles`` from the project root to list the catalog, or
``python -m puzzles 3`` to print puzzle #3 and its board.
"""
from puzzles.core import GOAL_TYPES, Puzzle, all_puzzles, get_puzzle

__all__ = ['GOAL_TYPES', 'Puzzle', 'all_puzzles', 'get_puzzle']
