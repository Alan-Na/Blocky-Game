"""The Puzzle type and lookups into the catalog."""
from __future__ import annotations

import random
from dataclasses import dataclass

from block import Block, generate_board
from goal import BlobGoal, Goal, PerimeterGoal
from settings import BOARD_SIZE, COLOUR_LIST, colour_name

GOAL_TYPES = {'blob': BlobGoal, 'perimeter': PerimeterGoal}


@dataclass(frozen=True)
class Puzzle:
    """A reproducible Blocky starting position.

    Attributes:
    - number: Stable number of this puzzle in the catalog.
    - name: Display name of this puzzle.
    - seed: Value passed to random.seed before the board is generated.
    - max_depth: Maximum depth of the board.
    - goal: Key into GOAL_TYPES, either 'blob' or 'perimeter'.
    - colour: Name of the target colour, as returned by settings.colour_name.
    - moves: Number of moves the player gets to improve the score.
    """
    number: int
    name: str
    seed: int
    max_depth: int
    goal: str
    colour: str
    moves: int

    def target_colour(self) -> tuple[int, int, int]:
        """Return the RGB value of this puzzle's target colour."""
        for colour in COLOUR_LIST:
            if colour_name(colour) == self.colour:
                return colour
        raise ValueError(f'unknown colour {self.colour!r}')

    def make_goal(self) -> Goal:
        """Return a new goal object for this puzzle."""
        return GOAL_TYPES[self.goal](self.target_colour())

    def build_board(self, size: int = BOARD_SIZE) -> Block:
        """Return this puzzle's starting board.

        The global state of the random module is restored afterwards, so
        building a puzzle never changes what the rest of the game draws.
        """
        saved = random.getstate()
        try:
            random.seed(self.seed)
            return generate_board(self.max_depth, size)
        finally:
            random.setstate(saved)

    def start_score(self, board: Block | None = None) -> int:
        """Return the goal score of the starting <board>."""
        if board is None:
            board = self.build_board()
        return self.make_goal().score(board)

    def max_score(self) -> int:
        """Return the highest score this puzzle's goal can reach."""
        cells = 2 ** self.max_depth
        if self.goal == 'perimeter':
            return 4 * cells  # corner cells count twice
        return cells * cells

    def describe(self) -> str:
        """Return a one-line summary of this puzzle."""
        return (f'#{self.number} {self.name}: {self.make_goal().description()} '
                f'Depth {self.max_depth}, {self.moves} moves, '
                f'starts at {self.start_score()}/{self.max_score()}.')


def all_puzzles() -> list[Puzzle]:
    """Return every puzzle in the catalog, in catalog order."""
    from puzzles.catalog import PUZZLES
    return list(PUZZLES)


def get_puzzle(number: int) -> Puzzle:
    """Return the puzzle with the given <number>.

    Raise KeyError if the catalog has no such puzzle.
    """
    for puzzle in all_puzzles():
        if puzzle.number == number:
            return puzzle
    raise KeyError(f'no puzzle #{number}')
