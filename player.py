from __future__ import annotations
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import Action, KEY_ACTION, ROTATE_CLOCKWISE, \
    ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE

COMPUTER_ACTIONS = [
    ROTATE_CLOCKWISE,
    ROTATE_COUNTER_CLOCKWISE,
    SWAP_HORIZONTAL,
    SWAP_VERTICAL,
    SMASH,
    COMBINE,
    PAINT
]


def create_players(num_human: int, num_random: int, smart_players: list[int]) \
        -> list[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.

    Player ids are given in the order that the players are created, starting
    at id 0.

    Each player is assigned a random goal.
    """
    total = num_human + num_random + len(smart_players)
    goals = generate_goals(total)

    players: list[Player] = []
    goal_index = 0
    next_id = 0

    for _ in range(num_human):
        players.append(HumanPlayer(next_id, goals[goal_index]))
        next_id += 1
        goal_index += 1

    for _ in range(num_random):
        players.append(RandomPlayer(next_id, goals[goal_index]))
        next_id += 1
        goal_index += 1

    for difficulty in smart_players:
        players.append(SmartPlayer(next_id, goals[goal_index], difficulty))
        next_id += 1
        goal_index += 1

    return players


def _get_block(block: Block, location: tuple[int, int], level: int) -> \
        Block | None:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - block.level <= level <= block.max_depth
    """
    x, y = location
    bx, by = block.position
    if not (bx <= x < bx + block.size and by <= y < by + block.size):
        return None

    if block.level == level or len(block.children) == 0:
        return block

    for child in block.children:
        result = _get_block(child, location, level)
        if result is not None:
            return result

    return block


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - id: This player's number.
    - goal: This player's assigned goal for the game.
    - penalty: The penalty accumulated by this player through their actions.
    """
    id: int
    goal: Goal
    penalty: int

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id
        self.penalty = 0

    def get_selected_block(self, board: Block) -> Block | None:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return a potential move to make on the <board>.

        The move is a tuple consisting of an action and
        the block the action will be applied to.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


class HumanPlayer(Player):
    """A human player.

    Instance Attributes:
    - _level: The level of the Block that the user selected most recently.
    - _desired_action: The most recent action that the user is attempting to do.

    Representation Invariants:
    - self._level >= 0
    """
    _level: int
    _desired_action: Action | None

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Block | None:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYUP:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level -= 1
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.

        This player's desired action gets reset after this method is called.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            self._correct_level(board)
            self._desired_action = None
            return None
        else:
            move = self._desired_action, block

            self._desired_action = None
            return move

    def _correct_level(self, board: Block) -> None:
        """Correct the level of the block that the player is currently
        selecting, if necessary.
        """
        self._level = max(0, min(self._level, board.max_depth))


class ComputerPlayer(Player):
    """A computer player. This class is still abstract,
    as how it generates moves is still to be defined
    in a subclass.

    Instance Attributes:
    - _proceed: True when the player should make a move, False when the
                player should wait.
    """
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)

        self._proceed = False

    def get_selected_block(self, board: Block) -> Block | None:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == pygame.BUTTON_LEFT):
            self._proceed = True

    # Note: this is included just to make pyTA happy; as it thinks
    #       we forgot to implement this abstract method otherwise :)
    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        raise NotImplementedError


class RandomPlayer(ComputerPlayer):
    """A computer player who chooses completely random moves."""

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None

        self._proceed = False

        moves = _valid_moves(board, self.goal.colour)
        if not moves:
            return PASS, board

        action, path = random.choice(moves)
        target = _block_from_path(board, path)

        return action, target


class SmartPlayer(ComputerPlayer):
    """A computer player who chooses moves by assessing a series of random
    moves and choosing the one that yields the best score.

    Private Instance Attributes:
    - _num_test: The number of moves this SmartPlayer will test out before
                 choosing a move.
    """
    _num_test: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        """Initialize this SmartPlayer with a <player_id> and <goal>.

        Use <difficulty> to determine and record how many moves this SmartPlayer
        will assess before choosing a move. The higher the value for
        <difficulty>, the more moves this SmartPlayer will assess, and hence the
        more difficult an opponent this SmartPlayer will be.

        Preconditions:
        - difficulty >= 0
        """
        super().__init__(player_id, goal)
        self._num_test = max(1, difficulty)

    def generate_move(self, board: Block) -> \
            tuple[Action, Block] | None:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None

        self._proceed = False

        current_score = self.goal.score(board)
        moves = _valid_moves(board, self.goal.colour)

        if not moves:
            return PASS, board

        best_move: tuple[Action, tuple[int, ...]] | None = None
        best_score = current_score

        for _ in range(self._num_test):
            action, path = random.choice(moves)
            board_copy = board.create_copy()
            block_copy = _block_from_path(board_copy, path)
            success = action.apply(block_copy, {'colour': self.goal.colour})
            if not success:
                continue

            score = self.goal.score(board_copy)
            if score > best_score:
                best_score = score
                best_move = (action, path)

        if best_move is None:
            return PASS, board

        action, path = best_move
        target = _block_from_path(board, path)
        return action, target


def _valid_moves(board: Block,
                 colour: tuple[int, int, int]) -> list[tuple[Action, tuple[int, ...]]]:
    """Return all valid non-pass moves available on <board>."""
    candidates: list[tuple[Action, tuple[int, ...]]] = []

    for block, path in _blocks_with_paths(board):
        for action in COMPUTER_ACTIONS:
            if not _is_potential_move(action, block, colour):
                continue

            board_copy = board.create_copy()
            target_copy = _block_from_path(board_copy, path)
            if action.apply(target_copy, {'colour': colour}):
                candidates.append((action, path))

    return candidates


def _is_potential_move(action: Action, block: Block,
                       colour: tuple[int, int, int]) -> bool:
    """Quick checks to skip obviously invalid actions."""
    if action in (ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
                  SWAP_HORIZONTAL, SWAP_VERTICAL):
        return len(block.children) != 0
    if action is SMASH:
        return block.smashable()
    if action is COMBINE:
        return len(block.children) != 0
    if action is PAINT:
        return (len(block.children) == 0 and block.level == block.max_depth
                and block.colour != colour)
    return True


def _blocks_with_paths(block: Block) -> list[tuple[Block, tuple[int, ...]]]:
    """Return all blocks paired with their path from <block>."""
    result: list[tuple[Block, tuple[int, ...]]] = []

    def helper(current: Block, path: tuple[int, ...]) -> None:
        result.append((current, path))
        for index, child in enumerate(current.children):
            helper(child, path + (index,))

    helper(block, ())
    return result


def _block_from_path(block: Block, path: tuple[int, ...]) -> Block:
    """Return the block reached by following <path> from <block>."""
    current = block
    for index in path:
        current = current.children[index]
    return current


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
