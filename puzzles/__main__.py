"""List the puzzle catalog, or show one puzzle: python -m puzzles [number]"""
from __future__ import annotations

import sys

from puzzles.core import all_puzzles, get_puzzle


def main(argv: list[str]) -> int:
    """Print the catalog, or the puzzle named by argv[1] and its board."""
    if len(argv) > 1:
        puzzle = get_puzzle(int(argv[1]))
        print(puzzle.describe())
        print(puzzle.build_board())
        return 0

    puzzles = all_puzzles()
    if not puzzles:
        print('The puzzle catalog is empty.')
    for puzzle in puzzles:
        print(puzzle.describe())
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
