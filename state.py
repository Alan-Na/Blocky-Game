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

This file contains the different game states for the Blocky game.
"""

from __future__ import annotations
import pygame

from actions import Action
from block import Block, _block_to_squares
from player import Player
from renderer import Renderer
from settings import ANIMATION_DURATION


class GameData:
    """
    A bundle of the data needed for a Blocky game.

    Instance Attributes:
    - max_turns: The maximum number of turns for the game.
    - board: The Blocky board on which this game will be played.
    - players: The entities that are playing this game.

    Representation Invariants:
    - len(self.players) >= 1
    - self.max_turns >= 1
    """
    max_turns: int
    board: Block
    players: list[Player]

    def __init__(self, board: Block, players: list[Player]) -> None:
        """Initialize the game data, saving a reference to <board> and
        <players>. The max_turns attribute is initially zero and will be later
        set by the actual game when it is played.

        Preconditions:
        - len(players) >= 1
        """
        self.max_turns = 0
        self.board = board
        self.players = players

    def calculate_score(self, player_id: int) -> tuple[int, int]:
        """Return a tuple containing first the <player_id>'s score based on
        their goal in the game and second the deductions from their score based
        on the actions they've taken.
        """
        goal_score = self.players[player_id].goal.score(self.board)

        penalty = self.players[player_id].penalty

        return goal_score, penalty


class GameState:
    """One of the different states that a Blocky game can be in.
    """

    def process_event(self, event: pygame.event.Event) -> None:
        """Process the event from the operating system, if possible.
        """
        raise NotImplementedError

    def update(self) -> GameState:
        """Update this GameState based on past events.

        Return the next GameState that should be updated. This can be self.
        """
        raise NotImplementedError

    def render(self, renderer: Renderer) -> None:
        """Render the current state of the game onto the screen.
        """
        raise NotImplementedError


class MainState(GameState):
    """A GameState that manages the moves made by different players in Blocky.

    Private Instance Attributes:
    - _turn: The current turn.
    - _data: A reference to the shared GameData.
    - _current_player_index: The index of the current player in GameData.players.
    - _current_score: The score of the current player, including penalties.
    """
    _turn: int
    _data: GameData
    _current_player_index: int
    _current_score: int

    def __init__(self, data: GameData) -> None:
        """Initialize this GameState.
        """
        self._turn = 0
        self._data = data
        self._current_player_index = 0

        score, penalty = self._data.calculate_score(self._current_player().id)
        self._current_score = score - penalty

    def _current_player(self) -> Player:
        """Return the player whose turn it is.
        """
        return self._data.players[self._current_player_index]

    def _update_player(self) -> None:
        """Update the player whose turn it is.
        """
        self._current_player_index = (self._current_player_index + 1) % len(
            self._data.players)

        score, penalty = self._data.calculate_score(self._current_player().id)
        self._current_score = score - penalty

        if self._current_player_index == 0:
            self._turn += 1

    def _do_move(self, move: tuple[Action, Block]) -> bool:
        """Attempt to do the player's requested <move>. If the move is
        successful, then the player's penalty is updated to reflect the
        cost of the action that was performed.

        Return True iff the action is successfully performed.
        """
        action, block = move
        player = self._current_player()

        move_successful = action.apply(block, {'colour': player.goal.colour})

        if move_successful:
            player.penalty += action.penalty
            self._update_player()

        return move_successful

    def process_event(self, event: pygame.event.Event) -> None:
        self._current_player().process_event(event)

    def update(self) -> GameState:
        if self._turn >= self._data.max_turns:
            return GameOverState(self._data)

        # Ask the player to make a move
        move = self._current_player().generate_move(self._data.board)

        if move is None:
            # No move was made, stay in the current state
            return self
        else:
            # Save what the board looks like before the move
            background = _block_to_squares(self._data.board)
            # Also save the current player ID
            player_id = self._current_player().id

            # Do the move
            if self._do_move(move):
                # Animate the move that was just done
                return AnimateMoveState(self, player_id, move, background)
            else:
                # The move was not valid, let the player try again
                return self

    def render(self, renderer: Renderer) -> None:
        renderer.draw_board(_block_to_squares(self._data.board))

        b = self._current_player().get_selected_block(self._data.board)
        if b is not None:
            renderer.highlight_block(b.position, b.size)

        p = self._current_player()
        p_type = str(p.__class__)
        p_type = p_type[p_type.index('.') + 1: -2]
        status = f'Turn {self._turn} | Player {p.id} ({p_type}) | ' \
                 f'Score {self._current_score} | {p.goal.description()}'
        renderer.draw_status(status)


class AnimateMoveState(GameState):
    """A GameState that animates a move made by a player before returning to its
    parent GameState.

    Private Instance Attributes:
    - _parent: The GameState to return to after the animation has completed.
    - _player_id: The ID of the player whose move is being animated.
    - _move: The move being animated.
    - _start_time: The time that the animation started.
    - _background: The board to display behind the animation.
    """
    _parent: GameState
    _player_id: int
    _move: tuple[Action, Block]
    _start_time: int
    _background: list[tuple[tuple[int, int, int], tuple[int, int], int]]

    def __init__(self, parent: GameState, player_id: int,
                 move: tuple[Action, Block],
                 background: list[tuple[tuple[int, int, int], tuple[int, int],
                                        int]]) -> None:
        """Initialize this GameState.
        """
        self._parent = parent
        self._player_id = player_id
        self._move = move
        self._background = background
        self._start_time = pygame.time.get_ticks()

    def process_event(self, event: pygame.event.Event) -> None:
        return  # Ignore the event

    def update(self) -> GameState:
        elapsed_seconds = (pygame.time.get_ticks() - self._start_time) / 1000

        if elapsed_seconds > ANIMATION_DURATION:
            # The animation is complete, do the move, go back to the last
            # GameState
            return self._parent
        else:
            # The animation is still running, remain in this GameState
            return self

    def render(self, renderer: Renderer) -> None:
        renderer.draw_board(self._background)

        # Draw an outline around the selected block
        b = self._move[1]
        renderer.highlight_block(b.position, b.size)

        # Draw the image representing the move
        action = self._move[0]
        renderer.draw_image(action, b.position, b.size)

        # Update the status message based on the action being performed.
        status = f'Player {self._player_id} is {action.message}'
        renderer.draw_status(status)


class GameOverState(GameState):
    """A GameState that is displayed when the game is over.

    Private Instance Attributes:
    - _scores: A list of tuples containing each player ID, goal score, and penalty
    - _winner: The ID of the winning player
    """
    _scores: list[tuple[int, int, int]]
    _winner: int

    def __init__(self, data: GameData) -> None:
        """Initialize this GameState.
        """
        self._scores = []
        for p in data.players:
            goal_score, penalty = data.calculate_score(p.id)
            self._scores.append((p.id, goal_score, penalty))
        self._winner = max(self._scores, key=lambda item: item[1] - item[2])[0]

    def process_event(self, event: pygame.event.Event) -> None:
        # Simply ignore the event
        return

    def update(self) -> GameState:
        # Nothing to change
        return self

    def render(self, renderer: Renderer) -> None:
        x = 10
        y = 10
        for t in self._scores:
            player_id, goal_score, penalty = t
            score = goal_score - penalty
            text = f'Player {player_id}\'s final score is {goal_score} - ' \
                   f'{penalty} = {score}'

            renderer.print(text, x, y)
            y += renderer.text_height()

        renderer.print(f'Player {self._winner} wins!', x, y)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['run_game'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'pygame', '__future__',
            'block', 'player', 'renderer', 'settings', 'actions'
        ],
        'generated-members': 'pygame.*'
    })
