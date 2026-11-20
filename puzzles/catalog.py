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
    Puzzle(number=7, name='Frozen Courtyard', seed=673022, max_depth=4,
           goal='blob', colour='Daffodil Delight', moves=7),
    Puzzle(number=8, name='Lonely Maze', seed=302584, max_depth=3,
           goal='perimeter', colour='Daffodil Delight', moves=6),
    Puzzle(number=9, name='Tangled Station', seed=181100, max_depth=3,
           goal='blob', colour='Daffodil Delight', moves=6),
    Puzzle(number=10, name='Frozen Ridge', seed=335386, max_depth=3,
           goal='perimeter', colour='Real Red', moves=5),
    Puzzle(number=11, name='Restless Harbor', seed=588213, max_depth=2,
           goal='blob', colour='Daffodil Delight', moves=4),
    Puzzle(number=12, name='Frozen Meadow', seed=884059, max_depth=3,
           goal='blob', colour='Daffodil Delight', moves=4),
    Puzzle(number=13, name='Restless Market', seed=968619, max_depth=3,
           goal='blob', colour='Old Olive', moves=6),
    Puzzle(number=14, name='Broken Terrace', seed=529862, max_depth=3,
           goal='perimeter', colour='Pacific Point', moves=5),
    Puzzle(number=15, name='Patient Mosaic', seed=86039, max_depth=2,
           goal='perimeter', colour='Daffodil Delight', moves=4),
    # New puzzles are appended above this line.
]
