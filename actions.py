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

This file contains the different actions that can be made by a Player.
"""
from __future__ import annotations
import pygame
from block import Block, ROT_CW, ROT_CCW, SWAP_HORZ, SWAP_VERT


class Action:
    """
    Abstract class representing an action that can be taken in the game.

    Subclasses specify the details of the action.
    """
    label: str
    message: str
    penalty: int
    short_name: str

    def __init__(self, name: str, label: str, msg: str, penalty: int) -> None:
        """
        Initialize this Action with the given <name>, <label>, <msg>, and
        <penalty>.
        """
        self.short_name = name
        self.label = label
        self.message = msg
        self.penalty = penalty

    def apply(self, block: Block, extra_info: dict) -> bool:
        """
        Apply this action to the given <block> and return True iff the action
        was successfully applied. <extra_info> contains additional
        values which implementations of apply may need.
        """
        raise NotImplementedError


class RotateClockwise(Action):
    """Rotate clockwise action"""
    def __init__(self) -> None:
        super().__init__('rotate-cw', 'Rotate Clockwise',
                         'rotating a block clockwise', 0)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.rotate(ROT_CW)


class RotateCounterClockwise(Action):
    """Rotate counterclockwise action"""
    def __init__(self) -> None:
        super().__init__('rotate-ccw', 'Rotate Counter Clockwise',
                         'rotating a block counter-clockwise', 0)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.rotate(ROT_CCW)


class SwapHorizontal(Action):
    """swap horizontal action"""
    def __init__(self) -> None:
        super().__init__('swap-horizontal', 'Swap Horizontally',
                         'swapping a block horizontally', 0)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.swap(SWAP_HORZ)


class SwapVertical(Action):
    """swap vertical action"""
    def __init__(self) -> None:
        super().__init__('swap-vertical', 'Swap Vertically',
                         'swapping a block vertically', 0)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.swap(SWAP_VERT)


class Smash(Action):
    """smash action"""
    def __init__(self) -> None:
        super().__init__('smash', 'Smash Block',
                         'smashing a block', 2)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.smash()


class Combine(Action):
    """combine action"""
    def __init__(self) -> None:
        super().__init__('combine', 'Combine Blocks',
                         'combining blocks', 1)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.combine()


class Paint(Action):
    """paint action"""
    def __init__(self) -> None:
        super().__init__('paint', 'Paint Blocks',
                         'painting blocks', 1)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return block.paint(extra_info['colour'])


class Pass(Action):
    """pass action"""
    def __init__(self) -> None:
        super().__init__('pass', 'Pass',
                         'passing', 0)

    def apply(self, block: Block, extra_info: dict) -> bool:
        return True


# Actions that can be performed in the game
ROTATE_CLOCKWISE = RotateClockwise()
ROTATE_COUNTER_CLOCKWISE = RotateCounterClockwise()
SWAP_HORIZONTAL = SwapHorizontal()
SWAP_VERTICAL = SwapVertical()
SMASH = Smash()
COMBINE = Combine()
PAINT = Paint()
PASS = Pass()

KEY_ACTION = {
    pygame.K_d: ROTATE_CLOCKWISE,
    pygame.K_a: ROTATE_COUNTER_CLOCKWISE,
    pygame.K_q: SWAP_HORIZONTAL,
    pygame.K_e: SWAP_VERTICAL,
    pygame.K_SPACE: SMASH,
    pygame.K_c: COMBINE,
    pygame.K_r: PAINT,
    pygame.K_TAB: PASS
}
