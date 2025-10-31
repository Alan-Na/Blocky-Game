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

This file contains some sample tests for Assignment 2.

Please use this as a starting point to check your work and write your own
tests!
"""
import pytest
from block import Block
from state import _block_to_squares
from goal import BlobGoal, PerimeterGoal, flatten, generate_goals
from player import _get_block, HumanPlayer, SmartPlayer, RandomPlayer, create_players
from settings import COLOUR_LIST
from actions import Action, KEY_ACTION, ROTATE_CLOCKWISE, \
    ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def set_children(block: Block, colours: list[tuple[int, int, int]] | None) \
        -> None:
    """Set the children at <level> for <block> using the given <colours>.

    Precondition:
        - len(colours) == 4
        - block.level + 1 <= block.max_depth
    """
    size = block.child_size()
    positions = block.children_positions()
    level = block.level + 1
    depth = block.max_depth

    block.children = []  # Potentially discard existing children!
    for i in range(4):
        b = Block(positions[i], size, colours[i], level, depth)
        block.children.append(b)


def board_1x1() -> Block:
    """Create a reference child block with a size of 750 and a max_depth of 0.
    """
    return Block((0, 0), 750, COLOUR_LIST[0], 0, 0)


def board_4x4() -> Block:
    """Create a reference board with a size of 750 and a max_depth of 2.
    """
    # Level 0
    board = Block((0, 0), 750, None, 0, 2)

    # Level 1
    colours = [None, COLOUR_LIST[2], COLOUR_LIST[1], COLOUR_LIST[3]]
    set_children(board, colours)

    # Level 2
    colours = [COLOUR_LIST[0], COLOUR_LIST[1], COLOUR_LIST[1], COLOUR_LIST[3]]
    set_children(board.children[0], colours)

    return board


def board_4x4_swap0() -> Block:
    """Create a reference board that is swapped along the horizontal plane.
    """
    # Level 0
    board = Block((0, 0), 750, None, 0, 2)

    # Level 1
    colours = [COLOUR_LIST[2], None, COLOUR_LIST[3], COLOUR_LIST[1]]
    set_children(board, colours)

    # Level 2
    colours = [COLOUR_LIST[0], COLOUR_LIST[1], COLOUR_LIST[1], COLOUR_LIST[3]]
    set_children(board.children[1], colours)

    return board


def board_4x4_rotate1() -> Block:
    """Create a reference board where the top-right block on level 1 has been
    rotated clockwise.
    """
    # Level 0
    board = Block((0, 0), 750, None, 0, 2)

    # Level 1
    colours = [None, COLOUR_LIST[2], COLOUR_LIST[1], COLOUR_LIST[3]]
    set_children(board, colours)

    # Level 2
    colours = [COLOUR_LIST[1], COLOUR_LIST[1], COLOUR_LIST[3], COLOUR_LIST[0]]
    set_children(board.children[0], colours)

    return board


def board_4x4_combine() -> Block:
    """Create a reference board with a size of 750 and a max_depth of 2.
    but with the original Level 2 board combined
    """
    # Level 0
    board = Block((0, 0), 750, None, 0, 2)

    # Level 1
    colours = [COLOUR_LIST[1], COLOUR_LIST[2], COLOUR_LIST[1], COLOUR_LIST[3]]
    set_children(board, colours)

    return board


def board_4x4_paint() -> Block:
    """Create a reference board with a size of 750 and a max_depth of 2
    but with a leaf painted.
    """
    # Level 0
    board = Block((0, 0), 750, None, 0, 2)

    # Level 1
    colours = [None, COLOUR_LIST[2], COLOUR_LIST[1], COLOUR_LIST[3]]
    set_children(board, colours)

    # Level 2
    colours = [COLOUR_LIST[0], COLOUR_LIST[1], COLOUR_LIST[2], COLOUR_LIST[3]]
    set_children(board.children[0], colours)

    return board


def flattened_board_4x4() -> list[list[tuple[int, int, int]]]:
    """Create a list of the unit cells inside the reference board."""
    return [
        [COLOUR_LIST[2], COLOUR_LIST[2], COLOUR_LIST[1], COLOUR_LIST[1]],
        [COLOUR_LIST[2], COLOUR_LIST[2], COLOUR_LIST[1], COLOUR_LIST[1]],
        [COLOUR_LIST[1], COLOUR_LIST[1], COLOUR_LIST[3], COLOUR_LIST[3]],
        [COLOUR_LIST[0], COLOUR_LIST[3], COLOUR_LIST[3], COLOUR_LIST[3]]
    ]


class TestBlockToSquares:
    """Tests for the _block_to_squares function"""

    def test_block_to_squares_leaf(self) -> None:
        """Test that a board with only one block can be correctly translated into
        a square that would be rendered onto the screen.
        """
        board = board_1x1()
        squares = _block_to_squares(board)
        expected = [(COLOUR_LIST[0], (0, 0), 750)]

        assert squares == expected

    def test_block_to_squares_reference(self) -> None:
        """Test that the reference board can be correctly translated into a set of
        squares that would be rendered onto the screen.
        """
        # The order the squares appear may differ based on the implementation, so
        # we use a set here.
        board = board_4x4()
        squares = _block_to_squares(board)
        expected = {((1, 128, 181), (563, 0), 188),
                    ((199, 44, 58), (375, 0), 188),
                    ((199, 44, 58), (375, 188), 188),
                    ((255, 211, 92), (563, 188), 188),
                    ((138, 151, 71), (0, 0), 375),
                    ((199, 44, 58), (0, 375), 375),
                    ((255, 211, 92), (375, 375), 375)
                    }

        assert set(squares) == expected
        assert len(squares) == len(expected)


class TestBlock:
    """A collection of methods that test the Block class.

    NOTE: this is a small subset of tests - just because you pass them does NOT
    mean you have a fully working implementation of the Block class.
    """

    def test_smash_on_child(self) -> None:
        """Test that a child block cannot be smashed.
        """
        board = board_1x1()
        board.smash()

        assert len(board.children) == 0
        assert board.colour == COLOUR_LIST[0]

    def test_smash_on_parent_with_no_children(self) -> None:
        """Test that a block not at max_depth and with no children can be
        smashed.
        """
        board = board_4x4()
        block = board.children[1]
        block.smash()

        assert len(block.children) == 4
        assert block.colour is None

        for child in block.children:
            # There should only be either 0 or 4 children (RI)
            assert len(child.children) == 0 or len(child.children) == 4
            if len(child.children) == 0:
                # A leaf should have a colour
                assert child.colour is not None
                # Colours should come from COLOUR_LIST
                assert child.colour in COLOUR_LIST
            elif len(child.children) == 4:
                # A parent should not have a colour
                assert child.colour is None

    def test_swap0(self) -> None:
        """Test that the reference board can be correctly swapped along the
        horizontal plane.
        """
        board = board_4x4()
        board.swap(0)
        expected = board_4x4_swap0()
        assert board == expected

    def test_rotate1(self) -> None:
        """Test that the top-right block of reference board on level 1 can be
        correctly rotated clockwise.
        """
        board = board_4x4()
        board.children[0].rotate(1)
        expected = board_4x4_rotate1()
        assert board == expected

    def test_paint(self) -> None:
        """Test that paint works correctly on a leaf."""
        board = board_4x4()
        expected = board_4x4_paint()

        cell = board.children[0].children[2]
        assert cell.paint(COLOUR_LIST[2]) is True
        assert board == expected

    def test_combine(self) -> None:
        """Test that combine works correctly when there is a majority colour
        amongst the children of a Block."""
        board = board_4x4()
        expected = board_4x4_combine()

        cell = board.children[0]
        assert cell.combine() is True
        assert board == expected

    def test_create_copy(self) -> None:
        """Test that create_copy works correctly on a 1x1 board"""
        board = board_1x1()
        copy = board.create_copy()
        assert id(board) != id(copy)
        assert board == copy


class TestPlayer:
    """A collection of methods for testing the methods and functions in the
    player module.

     NOTE: this is a small subset of tests - just because you pass them does NOT
     mean you have a fully working implementation.
    """

    def test_get_block_top_left(self) -> None:
        """Test that the correct block is retrieved from the reference board
        when requesting the top-left corner of the board.
        """
        board = board_4x4()
        top_left = (0, 0)
        assert _get_block(board, top_left, 0) == board
        assert _get_block(board, top_left, 1) == board.children[1]

    def test_get_block_top_right(self) -> None:
        """Test that the correct block is retrieved from the reference board
        when requesting the top-right corner of the board.
        """
        board = board_4x4()
        top_right = (board.size - 1, 0)
        assert _get_block(board, top_right, 0) == board
        assert _get_block(board, top_right, 1) == board.children[0]
        assert _get_block(board, top_right, 2) == \
               board.children[0].children[0]

    def test_generate_goals(self) -> None:
        """Test that generate_goals creates the correct number of goals and
        that no colours overlap."""
        goals = generate_goals(2)
        assert len(goals) == 2
        assert goals[0].colour != goals[1].colour

    def test_create_players(self) -> None:
        """Test that create_players creates the correct number of players
        and in the right order."""
        all_players = create_players(1, 2, [3])
        assert len(all_players) == 4

        # Check that the players are of the right type
        assert type(all_players[0]) == HumanPlayer
        assert type(all_players[1]) == RandomPlayer
        assert type(all_players[2]) == RandomPlayer
        assert type(all_players[3]) == SmartPlayer

        # Check that the players have the correct ids
        assert all_players[0].id == 0
        assert all_players[1].id == 1
        assert all_players[2].id == 2
        assert all_players[3].id == 3

    def test_random_player(self) -> None:
        """Test that RandomPlayer can be created correctly and that
        generate_move returns a move"""
        player = RandomPlayer(0, PerimeterGoal(COLOUR_LIST[0]))
        player._proceed = True
        board = board_4x4()
        move = player.generate_move(board)
        assert isinstance(move, tuple)
        assert isinstance(move[0], Action)
        assert isinstance(move[1], Block)

    def test_smart_player(self) -> None:
        """Test that SmartPlayer can be created correctly and that
        generate_move returns a move.

        Does *not* check whether the move is a good one or not, however.
        """
        player = SmartPlayer(0, PerimeterGoal(COLOUR_LIST[3]), 10)
        player._proceed = True
        board = board_4x4()
        move = player.generate_move(board)
        assert isinstance(move, tuple)
        assert isinstance(move[0], Action)
        assert isinstance(move[1], Block)


class TestGoal:
    """A collection of methods for testing the sub-classes of Goal.

     NOTE: this is a small subset of tests - just because you pass them does NOT
     mean you have a fully working implementation of the Goal sub-classes.
    """

    def test_block_flatten_reference(self) -> None:
        """Test that flattening the reference board results in the expected list
        of colours.
        """
        board = board_4x4()
        result = flatten(board)

        # We are expected a "square" 2D list
        for sublist in result:
            assert len(result) == len(sublist)

        assert result == flattened_board_4x4()

    def test_blob_size(self) -> None:
        """Test that the undiscovered_blob_size returns the correct size
        """
        board = flattened_board_4x4()
        print(board_4x4())
        position = (3, 3)
        # Create visited such that all cells are -1
        visited = [[-1 for _ in row] for row in board]

        # Set up a goal for each colour and check the results
        goal = BlobGoal(COLOUR_LIST[3])
        assert goal._undiscovered_blob_size(position, board, visited) == 5

        # After calling _undiscovered_blob_size, visited should have 1s for
        # all the connected cells of the same colour and 0s on
        # connected cells of a different colour.
        # Cells that are connected to an un-connected colour should remain
        # unchanged.
        expected_visited = [[-1, -1, -1, -1], [-1, -1, 0, 0],
                            [-1, 0, 1, 1], [0, 1, 1, 1]]
        assert visited == expected_visited

    def test_blob_goal_reference(self) -> None:
        """Test that the blob goal score for each colour in the reference board
        is correct.
        """
        board = board_4x4()
        correct_scores = [
            (COLOUR_LIST[0], 1),
            (COLOUR_LIST[1], 4),
            (COLOUR_LIST[2], 4),
            (COLOUR_LIST[3], 5)
        ]

        # Set up a goal for each colour and check the results
        for colour, expected in correct_scores:
            goal = BlobGoal(colour)
            assert goal.score(board) == expected

    def test_perimeter_goal_reference(self):
        """Test that the perimeter goal score for each colour in the reference
        board is correct.
        """
        board = board_4x4()
        correct_scores = [
            (COLOUR_LIST[0], 2),
            (COLOUR_LIST[1], 5),
            (COLOUR_LIST[2], 4),
            (COLOUR_LIST[3], 5)
        ]

        # Set up a goal for each colour and check results.
        for colour, expected in correct_scores:
            goal = PerimeterGoal(colour)
            assert goal.score(board) == expected

    def test_perimeter_goal_one_unit_cell(self):
        """Test that the perimeter goal score for each colour of a 1x1 board
        is correct.
        """
        board = board_1x1()
        correct_scores = [
            (COLOUR_LIST[0], 4),
            (COLOUR_LIST[1], 0),
            (COLOUR_LIST[2], 0),
            (COLOUR_LIST[3], 0)
        ]

        # Set up a goal for each colour and check results.
        for colour, expected in correct_scores:
            goal = PerimeterGoal(colour)
            assert goal.score(board) == expected


if __name__ == '__main__':
    pytest.main(['example_tests.py'])
