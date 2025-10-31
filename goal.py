"""CSC148 Assignment 2

CSC148 Winter 2024
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
Jaisie Sin, and Joonho Kim

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, Jaisie Sin, and Joonho Kim

Module Description:

This file contains the hierarchy of Goal classes and related helper functions.
"""
from __future__ import annotations
import random
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> list[Goal]:
    """Return a randomly generated list of goals with length <num_goals>.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Preconditions:
    - num_goals <= len(COLOUR_LIST)
    """
    if num_goals == 0:
        return []

    goal_type = random.choice([PerimeterGoal, BlobGoal])
    colours = random.sample(COLOUR_LIST, num_goals)

    return [goal_type(colour) for colour in colours]


def flatten(block: Block) -> list[list[tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j].

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    size = 2 ** (block.max_depth - block.level)
    grid: list[list[tuple[int, int, int]]] = [
        [block.colour for _ in range(size)] for _ in range(size)
    ]

    def _fill(b: Block, x: int, y: int, span: int) -> None:
        if len(b.children) == 0:
            for i in range(x, x + span):
                for j in range(y, y + span):
                    grid[i][j] = b.colour
        else:
            half = span // 2
            _fill(b.children[1], x, y, half)
            _fill(b.children[0], x + half, y, half)
            _fill(b.children[2], x, y + half, half)
            _fill(b.children[3], x + half, y + half, half)

    _fill(block, 0, 0, size)

    return grid


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - colour: The target colour for this goal, that is the colour to which
              this goal applies.
    """
    colour: tuple[int, int, int]

    def __init__(self, target_colour: tuple[int, int, int]) -> None:
        """Initialize this goal to have the given <target_colour>.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given <board>.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A goal to maximize the presence of this goal's target colour
    on the board's perimeter.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a PerimeterGoal is defined to be the number of unit cells
        on the perimeter whose colour is this goal's target colour. Corner cells
        count twice toward the score.
        """
        grid = flatten(board)
        size = len(grid)

        score = 0
        for x in range(size):
            if grid[x][0] == self.colour:
                score += 1
            if grid[x][size - 1] == self.colour:
                score += 1

        for y in range(size):
            if grid[0][y] == self.colour:
                score += 1
            if grid[size - 1][y] == self.colour:
                score += 1

        return score

    def description(self) -> str:
        """Return a description of this goal.
        """
        colour = colour_name(self.colour)
        return (f'Aim for {colour} along the perimeter; corners count twice.')


class BlobGoal(Goal):
    """A goal to create the largest connected blob of this goal's target
    colour, anywhere within the Block.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a BlobGoal is defined to be the total number of
        unit cells in the largest connected blob within this Block.
        """
        grid = flatten(board)
        size = len(grid)
        visited = [[-1 for _ in range(size)] for _ in range(size)]

        best = 0
        for x in range(size):
            for y in range(size):
                if visited[x][y] == -1 and grid[x][y] == self.colour:
                    blob_size = self._undiscovered_blob_size((x, y), grid,
                                                             visited)
                    if blob_size > best:
                        best = blob_size

        return best

    def _undiscovered_blob_size(self, pos: tuple[int, int],
                                board: list[list[tuple[int, int, int]]],
                                visited: list[list[int]]) -> int:
        """Return the size of the largest connected blob in <board> that (a) is 
        of this Goal's target <colour>, (b) includes the cell at <pos>, and (c)
        involves only cells that are not in <visited>.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure (to <board>) that, in each cell,
        contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.

        If <pos> is out of bounds for <board>, return 0.
        """
        x, y = pos
        if x < 0 or y < 0:
            return 0
        if x >= len(board) or y >= len(board):
            return 0

        if visited[x][y] != -1:
            return 0

        if board[x][y] != self.colour:
            visited[x][y] = 0
            return 0

        visited[x][y] = 1
        size = 1
        for neighbour in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            size += self._undiscovered_blob_size(neighbour, board, visited)

        return size

    def description(self) -> str:
        """Return a description of this goal.
        """
        colour = colour_name(self.colour)
        return f'Build the largest connected blob of {colour} blocks.'


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
