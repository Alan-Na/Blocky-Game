from __future__ import annotations

import random
from typing import Dict

from actions import Action
from block import Block, generate_board
from goal import Goal, flatten
from move_utils import list_valid_moves, block_from_path
from settings import BOARD_SIZE


class ReinforcementLearner:
    """A tiny reinforcement learner used to guide advanced SmartPlayers.

    The learner uses a simple linear function approximator trained with TD(0)
    updates on randomly generated boards. The learned weights provide a value
    estimate for any board relative to the player's goal colour.
    """

    _goal: Goal
    _learning_rate: float
    _discount: float
    _episodes: int
    _steps_per_episode: int
    _weights: Dict[str, float]

    def __init__(self, goal: Goal, difficulty: int) -> None:
        self._goal = goal
        self._learning_rate = 0.08
        self._discount = 0.86
        # Scale the amount of self-play based on the requested difficulty.
        self._episodes = 30 + max(0, difficulty) * 8
        self._steps_per_episode = 4 + max(1, difficulty)
        self._weights = {
            'bias': 0.0,
            'normalized_score': 0.0,
            'colour_fraction': 0.0,
            'perimeter_fraction': 0.0,
            'central_fraction': 0.0
        }
        self._train()

    @property
    def discount(self) -> float:
        return self._discount

    def evaluate(self, board: Block) -> float:
        """Return the current value estimate for <board>."""
        features = self._features(board)
        return sum(self._weights[name] * value for name, value in features.items())

    def _train(self) -> None:
        """Run a lightweight TD(0) training loop on random boards."""
        for _ in range(self._episodes):
            board = generate_board(3, min(BOARD_SIZE, 320))
            for _ in range(self._steps_per_episode):
                features = self._features(board)
                value = sum(self._weights[n] * v for n, v in features.items())
                moves = list_valid_moves(board, self._goal.colour)
                if not moves:
                    break

                action, path = random.choice(moves)
                next_board = board.create_copy()
                target_block = block_from_path(next_board, path)
                if not action.apply(target_block, {'colour': self._goal.colour}):
                    break

                reward = (self._goal.score(next_board)
                          - self._goal.score(board)
                          - action.penalty)
                next_features = self._features(next_board)
                next_value = sum(self._weights[n] * v for n, v in next_features.items())
                td_target = reward + self._discount * next_value
                td_error = td_target - value

                for name, val in features.items():
                    self._weights[name] += self._learning_rate * td_error * val

                board = next_board

    def _features(self, board: Block) -> Dict[str, float]:
        """Extract simple, goal-aware features for <board>."""
        grid = flatten(board)
        size = len(grid)
        if size == 0:
            return {'bias': 1.0, 'normalized_score': 0.0,
                    'colour_fraction': 0.0, 'perimeter_fraction': 0.0,
                    'central_fraction': 0.0}

        height = len(grid[0])
        total_cells = max(1, size * height)

        goal_colour = self._goal.colour
        colour_count = 0
        perimeter_count = 0
        central_count = 0

        for x in range(size):
            for y in range(height):
                cell_colour = grid[x][y]
                if cell_colour == goal_colour:
                    colour_count += 1
                    if 0 < x < size - 1 and 0 < y < height - 1:
                        central_count += 1
                if x in (0, size - 1) or y in (0, height - 1):
                    if cell_colour == goal_colour:
                        perimeter_count += 1

        perimeter_total = max(1, size * 2 + height * 2 - 4)
        central_total = max(1, (size - 2) * (height - 2))

        normalized_score = self._goal.score(board) / total_cells
        colour_fraction = colour_count / total_cells
        perimeter_fraction = perimeter_count / perimeter_total
        central_fraction = central_count / central_total

        return {
            'bias': 1.0,
            'normalized_score': normalized_score,
            'colour_fraction': colour_fraction,
            'perimeter_fraction': perimeter_fraction,
            'central_fraction': central_fraction
        }
