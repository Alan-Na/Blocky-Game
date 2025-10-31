from __future__ import annotations
import math
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
    colours = random.sample(COLOUR_LIST, k=num_goals)
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
    span = 2 ** (block.max_depth - block.level)

    if len(block.children) == 0:
        assert block.colour is not None
        return [[block.colour for _ in range(span)] for _ in range(span)]

    half = span // 2
    flattened_children = [flatten(child) for child in block.children]

    combined: list[list[tuple[int, int, int]]] = []
    for col in range(span):
        if col < half:
            top = flattened_children[1][col]
            bottom = flattened_children[2][col]
        else:
            child_col = col - half
            top = flattened_children[0][child_col]
            bottom = flattened_children[3][child_col]
        combined.append(top + bottom)

    return combined


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

        if not grid:
            return 0

        width = len(grid)
        height = len(grid[0])
        score = 0

        for x in range(width):
            if grid[x][0] == self.colour:
                score += 1
            if grid[x][height - 1] == self.colour:
                score += 1

        for y in range(height):
            if grid[0][y] == self.colour:
                score += 1
            if grid[width - 1][y] == self.colour:
                score += 1

        return score

    def description(self) -> str:
        """Return a description of this goal.
        """
        return f'Perimeter goal: maximize {colour_name(self.colour)} on edge cells.'


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
        if not grid:
            return 0

        visited = [[-1 for _ in column] for column in grid]
        best = 0

        for x in range(len(grid)):
            for y in range(len(grid[x])):
                if visited[x][y] == -1:
                    size = self._undiscovered_blob_size((x, y), grid, visited)
                    best = max(best, size)

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
        width = len(board)
        if width == 0:
            return 0
        height = len(board[0])

        if not (0 <= x < width and 0 <= y < height):
            return 0

        if visited[x][y] != -1:
            return 0

        if board[x][y] != self.colour:
            visited[x][y] = 0
            return 0

        visited[x][y] = 1
        size = 1

        neighbours = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        for nx, ny in neighbours:
            size += self._undiscovered_blob_size((nx, ny), board, visited)

        return size

    def description(self) -> str:
        """Return a description of this goal.
        """
        return f'Blob goal: build the largest {colour_name(self.colour)} region.'


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
