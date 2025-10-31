from __future__ import annotations
import pygame

from typing import Any

from actions import Action
from block import Block, _block_to_squares, generate_board
from player import Player, create_players
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

    def build_scoreboard_entries(self) -> list[dict[str, Any]]:
        """Return compact scoreboard data for each player."""
        entries: list[dict[str, Any]] = []
        for player in self.players:
            goal_score, penalty = self.calculate_score(player.id)
            total = goal_score - penalty
            entries.append({
                'id': player.id,
                'score': total,
                'goal_colour': getattr(player.goal, 'colour', None)
            })

        return entries


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


class StartMenuState(GameState):
    """The start screen shown before the main game begins."""

    _data: GameData
    _buttons: dict[str, pygame.Rect]
    _hover: str | None
    _pending: str | None
    _options: list[str]

    def __init__(self, data: GameData) -> None:
        self._data = data
        self._buttons = {}
        self._hover = None
        self._pending = None
        self._options = ['Play Game', 'Instructions']

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._refresh_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            self._handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._pending = 'play'
            elif event.key == pygame.K_i:
                self._pending = 'instructions'

    def update(self) -> GameState:
        if self._pending == 'play':
            self._pending = None
            return ModeSelectState(self._data, self)
        if self._pending == 'instructions':
            self._pending = None
            return InstructionState(self._data, self)
        return self

    def render(self, renderer: Renderer) -> None:
        message = 'Click a button or press ENTER to start.'
        buttons = renderer.draw_menu(
            'Blocky: Architect Edition',
            'Shape the board, chase your goal, and outscore your rivals.',
            self._options,
            self._hover
        )
        self._buttons = buttons
        previous_hover = self._hover
        self._refresh_hover(pygame.mouse.get_pos())
        if self._hover != previous_hover:
            self._buttons = renderer.draw_menu(
                'Blocky: Architect Edition',
                'Shape the board, chase your goal, and outscore your rivals.',
                self._options,
                self._hover
            )
        renderer.draw_status(message)

    def reset_menu(self) -> None:
        """Reset stored UI state when returning from other screens."""
        self._pending = None
        self._hover = None
        self._buttons = {}

    def _handle_click(self, pos: tuple[int, int]) -> None:
        label = self._label_at(pos)
        if label == 'Play Game':
            self._pending = 'play'
        elif label == 'Instructions':
            self._pending = 'instructions'

    def _refresh_hover(self, pos: tuple[int, int]) -> None:
        self._hover = self._label_at(pos)

    def _label_at(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self._buttons.items():
            if rect.collidepoint(pos):
                return label
        return None


class ModeSelectState(GameState):
    """State that lets the user choose the desired game mode."""

    _data: GameData
    _parent: StartMenuState
    _buttons: dict[str, pygame.Rect]
    _hover: str | None
    _pending: str | None
    _options: list[str]

    def __init__(self, data: GameData, parent: StartMenuState) -> None:
        self._data = data
        self._parent = parent
        self._buttons = {}
        self._hover = None
        self._pending = None
        self._options = [
            'Player vs Player',
            'Player vs Computer (Basic AI)',
            'Player vs Computer (Reinforced AI)',
            'Back to Main Menu'
        ]

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._refresh_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            self._handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                mapping = {
                    'Player vs Player': 'pvp',
                    'Player vs Computer (Basic AI)': 'pvc_basic',
                    'Player vs Computer (Reinforced AI)': 'pvc_reinforced',
                    'Back to Main Menu': 'back'
                }
                if self._hover in mapping:
                    self._pending = mapping[self._hover]
            elif event.key == pygame.K_ESCAPE:
                self._pending = 'back'

    def update(self) -> GameState:
        if self._pending == 'pvp':
            self._pending = None
            return self._start_mode(num_human=2, num_random=0,
                                    smart_levels=[], reinforced_levels=[])
        if self._pending == 'pvc_basic':
            self._pending = None
            return self._start_mode(num_human=1, num_random=0,
                                    smart_levels=[6], reinforced_levels=[])
        if self._pending == 'pvc_reinforced':
            self._pending = None
            return self._start_mode(num_human=1, num_random=0,
                                    smart_levels=[], reinforced_levels=[8])
        if self._pending == 'back':
            self._pending = None
            self._parent.reset_menu()
            return self._parent
        return self

    def render(self, renderer: Renderer) -> None:
        buttons = renderer.draw_menu(
            'Select Game Mode',
            'Choose how you want to play this match.',
            self._options,
            self._hover
        )
        self._buttons = buttons
        previous_hover = self._hover
        self._refresh_hover(pygame.mouse.get_pos())
        if self._hover != previous_hover:
            self._buttons = renderer.draw_menu(
                'Select Game Mode',
                'Choose how you want to play this match.',
                self._options,
                self._hover
            )
        status = 'Press ENTER to confirm. ESC returns to the main menu.'
        renderer.draw_status(status)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        label = self._label_at(pos)
        mapping = {
            'Player vs Player': 'pvp',
            'Player vs Computer (Basic AI)': 'pvc_basic',
            'Player vs Computer (Reinforced AI)': 'pvc_reinforced',
            'Back to Main Menu': 'back'
        }
        if label in mapping:
            self._pending = mapping[label]

    def _refresh_hover(self, pos: tuple[int, int]) -> None:
        self._hover = self._label_at(pos)

    def _label_at(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self._buttons.items():
            if rect.collidepoint(pos):
                return label
        return None

    def _start_mode(self, num_human: int, num_random: int,
                    smart_levels: list[int],
                    reinforced_levels: list[int]) -> GameState:
        depth = self._data.board.max_depth
        root_size = self._data.board.size
        self._data.board = generate_board(depth, root_size)
        self._data.players = create_players(num_human, num_random,
                                            smart_levels, reinforced_levels)
        return MainState(self._data)


class InstructionState(GameState):
    """Modal instructions that can be opened from the start menu."""

    _data: GameData
    _parent: StartMenuState
    _back_rect: pygame.Rect | None
    _hover: bool
    _return_to_menu: bool
    _lines: list[str]
    _scroll_offset: int
    _max_scroll: int

    def __init__(self, data: GameData, parent: StartMenuState) -> None:
        self._data = data
        self._parent = parent
        self._back_rect = None
        self._hover = False
        self._return_to_menu = False
        self._scroll_offset = 0
        self._max_scroll = 0
        self._lines = [
            'Welcome to Blocky!',
            '',
            'Objective:',
            ' - Shape the shared board so your goal colour leads the pack.',
            ' - Each player receives a random goal card: Perimeter or Blob.',
            '',
            'Turn Structure:',
            ' - Hover the mouse to pick a block. W / S change the focus depth.',
            ' - Press the action keys shown on the right to take one move.',
            ' - Actions with penalties subtract points from your final total.',
            '',
            'Available Actions:',
            ' - Rotate / Swap: Reposition quadrants without spending points.',
            ' - Smash (penalty 2): Split a block into four fresh children.',
            ' - Paint (penalty 1): Recolour a leaf block to your goal colour.',
            ' - Combine (penalty 1): Merge four matching children into one.',
            ' - Pass: Skip your move when every option would hurt.',
            '',
            'Scoring Breakdown:',
            ' - Perimeter Goal: +1 for each edge cell, corners are worth +2.',
            ' - Blob Goal: Points equal the size of your largest connected blob.',
            ' - Final Score = Goal Points minus all penalties you incurred.',
            '',
            'Helpful Tips:',
            ' - Use rotate and swap to stage colours before smash or paint.',
            ' - Trigger computer turns with a left click during their turn.',
            ' - After the set rounds, the best final score wins the match.',
            ' - Reinforced AI studies self-play to spot long-term improvements.'
        ]

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            if self._back_rect is not None and self._back_rect.collidepoint(event.pos):
                self._return_to_menu = True
        elif event.type == pygame.MOUSEWHEEL:
            self._adjust_scroll(-event.y * 50)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE,
                             pygame.K_RETURN, pygame.K_SPACE):
                self._return_to_menu = True
            elif event.key == pygame.K_DOWN:
                self._adjust_scroll(40)
            elif event.key == pygame.K_UP:
                self._adjust_scroll(-40)
            elif event.key == pygame.K_PAGEDOWN:
                self._adjust_scroll(160)
            elif event.key == pygame.K_PAGEUP:
                self._adjust_scroll(-160)

    def update(self) -> GameState:
        if self._return_to_menu:
            self._return_to_menu = False
            self._back_rect = None
            self._hover = False
            self._scroll_offset = 0
            self._max_scroll = 0
            self._parent.reset_menu()
            return self._parent
        return self

    def render(self, renderer: Renderer) -> None:
        footer = 'Press ESC, ENTER, or click Back to return to the main menu.'
        back_rect, max_scroll, applied_offset = renderer.draw_instruction_screen(
            'How to Play',
            self._lines,
            'Back',
            self._hover,
            self._scroll_offset,
            footer
        )
        self._back_rect = back_rect
        self._max_scroll = max_scroll
        self._scroll_offset = applied_offset
        previous = self._hover
        self._update_hover(pygame.mouse.get_pos())
        if self._hover != previous:
            back_rect, max_scroll, applied_offset = renderer.draw_instruction_screen(
                'How to Play',
                self._lines,
                'Back',
                self._hover,
                self._scroll_offset,
                footer
            )
            self._back_rect = back_rect
            self._max_scroll = max_scroll
            self._scroll_offset = applied_offset
        renderer.draw_status('Review the guide, then head back to start a game.')

    def _update_hover(self, pos: tuple[int, int]) -> None:
        if self._back_rect is None:
            self._hover = False
        else:
            self._hover = self._back_rect.collidepoint(pos)

    def _adjust_scroll(self, delta: int) -> None:
        if delta == 0:
            return
        self._scroll_offset = max(0, min(self._scroll_offset + delta, self._max_scroll))


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
                return AnimateMoveState(self, player_id, move, background, self._data)
            else:
                # The move was not valid, let the player try again
                return self

    def render(self, renderer: Renderer) -> None:
        renderer.draw_board(_block_to_squares(self._data.board))

        b = self._current_player().get_selected_block(self._data.board)
        if b is not None:
            renderer.highlight_block(b.position, b.size)

        renderer.draw_scoreboard(
            self._data.build_scoreboard_entries(),
            self._current_player().id
        )
        renderer.draw_instruction_panel()

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

    _data: GameData

    def __init__(self, parent: GameState, player_id: int,
                 move: tuple[Action, Block],
                 background: list[tuple[tuple[int, int, int], tuple[int, int],
                                        int]],
                 data: GameData) -> None:
        """Initialize this GameState.
        """
        self._parent = parent
        self._player_id = player_id
        self._move = move
        self._background = background
        self._start_time = pygame.time.get_ticks()
        self._data = data

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

        renderer.draw_scoreboard(
            self._data.build_scoreboard_entries(),
            self._player_id
        )
        renderer.draw_instruction_panel()

        # Update the status message based on the action being performed.
        status = f'Player {self._player_id} is {action.message}'
        renderer.draw_status(status)


class GameOverState(GameState):
    """A GameState that is displayed when the game is over.

    Private Instance Attributes:
    - _scores: A list of tuples containing each player ID, goal score, and penalty
    - _winner: The ID of the winning player
    - _entries: Cached scoreboard entries for rendering overlays
    """
    _scores: list[tuple[int, int, int]]
    _winner: int
    _entries: list[dict[str, Any]]

    def __init__(self, data: GameData) -> None:
        """Initialize this GameState.
        """
        self._scores = []
        for p in data.players:
            goal_score, penalty = data.calculate_score(p.id)
            self._scores.append((p.id, goal_score, penalty))
        self._winner = max(self._scores, key=lambda item: item[1] - item[2])[0]
        self._entries = data.build_scoreboard_entries()

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
        renderer.draw_scoreboard(self._entries, self._winner)
        renderer.draw_instruction_panel()


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
