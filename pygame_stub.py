"""Lightweight pygame compatibility layer for headless testing environments.

This module provides a tiny subset of the pygame API that is sufficient for
running the automated logic tests in environments where the real pygame package
is not available (such as the execution sandbox used for grading).  Whenever the
actual pygame package is installed, project modules load it instead of this
stub, so the graphical game keeps working without any changes.
"""
from __future__ import annotations

from dataclasses import dataclass
import time as _time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Sequence

__all__ = [
    'Surface', 'Rect', 'font', 'display', 'draw', 'transform', 'event', 'time',
    'mouse', 'image', 'key', 'Clock', 'init', 'quit', 'K_d', 'K_a', 'K_q',
    'K_e', 'K_SPACE', 'K_c', 'K_r', 'K_TAB', 'BUTTON_LEFT', 'QUIT', 'KEYUP',
    'MOUSEBUTTONDOWN', 'SRCALPHA'
]


# ---------------------------------------------------------------------------
# Core geometry primitives
# ---------------------------------------------------------------------------
@dataclass
class Rect:
    """A minimal stand-in for ``pygame.Rect``."""
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def copy(self) -> 'Rect':
        return Rect(self.x, self.y, self.width, self.height)

    def __iter__(self) -> Iterable[int]:
        return iter((self.x, self.y, self.width, self.height))


class Surface:
    """A simplified surface that records its size and allows no-op drawing."""

    def __init__(self, size: tuple[int, int] = (0, 0), flags: int | None = None) -> None:
        self._width, self._height = size
        self._colour = (0, 0, 0, 0)

    def fill(self, colour: Sequence[int]) -> None:
        self._colour = tuple(colour)

    def blit(self, source: 'Surface', dest: tuple[int, int]) -> None:  # pragma: no cover - noop
        _ = source, dest

    def copy(self) -> 'Surface':
        return Surface((self._width, self._height))

    def get_rect(self) -> Rect:
        return Rect(0, 0, self._width, self._height)

    def get_size(self) -> tuple[int, int]:
        return self._width, self._height

    def get_width(self) -> int:
        return self._width

    def get_height(self) -> int:
        return self._height


# ---------------------------------------------------------------------------
# Font handling
# ---------------------------------------------------------------------------
class _Font:
    def __init__(self, _name: str | None, size: int) -> None:
        self._size = size
        self._bold = False

    def render(self, text: str, _antialias: bool, _colour: Sequence[int]) -> Surface:
        # Approximate the width: it does not matter for tests, we just need a Surface.
        width = max(1, int(len(text) * self._size * 0.6))
        return Surface((width, self._size))

    def set_bold(self, bold: bool) -> None:
        self._bold = bold

    def get_height(self) -> int:
        return self._size


def _get_default_font() -> str:
    return 'default-font'


font = SimpleNamespace(Font=_Font, get_default_font=_get_default_font)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _noop(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - pure stub
    return None


draw = SimpleNamespace(rect=_noop, line=_noop)
transform = SimpleNamespace(smoothscale=lambda surface, size: Surface(size))


# ---------------------------------------------------------------------------
# Display, events, and timing
# ---------------------------------------------------------------------------
class _Display:
    def set_mode(self, size: tuple[int, int]) -> Surface:
        return Surface(size)

    def set_caption(self, _title: str) -> None:
        return None

    def flip(self) -> None:  # pragma: no cover - noop
        return None


display = _Display()


class Event:
    def __init__(self, type_: int, **attrs: Any) -> None:
        self.type = type_
        for key, value in attrs.items():
            setattr(self, key, value)


def _get_events() -> list['Event']:
    return []


event = SimpleNamespace(Event=Event, get=_get_events)


class Clock:
    def tick(self, _fps: int = 0) -> None:  # pragma: no cover - noop
        return None


def _get_ticks() -> int:
    return int((_time.time() - _START_TIME) * 1000)


time = SimpleNamespace(get_ticks=_get_ticks, Clock=Clock)


class _Mouse:
    def get_pos(self) -> tuple[int, int]:
        return (0, 0)


mouse = _Mouse()


class _Image:
    def save(self, _surface: Surface, filename: str) -> None:
        Path(filename).write_bytes(b'')


image = _Image()


class _Key:
    _lookup = {
        ord('d'): 'd',
        ord('a'): 'a',
        ord('q'): 'q',
        ord('e'): 'e',
        ord(' '): 'space',
        ord('c'): 'c',
        ord('r'): 'r',
        9: 'tab'
    }

    def name(self, key: int) -> str:
        return self._lookup.get(key, str(key))


key = _Key()


def init() -> tuple[int, int]:  # pragma: no cover - noop
    return (0, 0)


def quit() -> None:  # pragma: no cover - noop
    return None


# ---------------------------------------------------------------------------
# Constants used across the codebase
# ---------------------------------------------------------------------------
K_d = ord('d')
K_a = ord('a')
K_q = ord('q')
K_e = ord('e')
K_SPACE = ord(' ')
K_c = ord('c')
K_r = ord('r')
K_TAB = 9
BUTTON_LEFT = 1
QUIT = 12
KEYUP = 13
MOUSEBUTTONDOWN = 14
SRCALPHA = 0

_START_TIME = _time.time()
