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
    Puzzle(number=3, name='Lucky Lantern', seed=637970, max_depth=3,
           goal='blob', colour='Old Olive', moves=4),
    Puzzle(number=4, name='Copper Atrium', seed=843365, max_depth=3,
           goal='perimeter', colour='Real Red', moves=7),
    Puzzle(number=5, name='Narrow Maze', seed=206377, max_depth=4,
           goal='blob', colour='Old Olive', moves=5),
    Puzzle(number=6, name='Lonely Orchard', seed=515449, max_depth=2,
           goal='blob', colour='Daffodil Delight', moves=4),
    # New puzzles are appended above this line.
]
