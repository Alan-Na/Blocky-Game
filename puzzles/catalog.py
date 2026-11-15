"""The catalog of Blocky puzzles.

Puzzles are only ever appended, so a puzzle number always refers to the same
starting position. Run ``python -m puzzles`` to list them.
"""
from __future__ import annotations

from puzzles.core import Puzzle

PUZZLES: list[Puzzle] = [
    Puzzle(number=1, name='Narrow Market', seed=1641, max_depth=4,
           goal='blob', colour='Old Olive', moves=6),
    Puzzle(number=2, name='Crimson Harbor', seed=772799, max_depth=4,
           goal='blob', colour='Real Red', moves=9),
    # New puzzles are appended above this line.
]
