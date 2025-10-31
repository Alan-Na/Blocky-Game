from typing import Any, cast

import pygame

from actions import Action, KEY_ACTION
from settings import (BACKGROUND_COLOUR, TEXT_COLOUR, OUTLINE_THICKNESS,
                      OUTLINE_COLOUR, HIGHLIGHT_THICKNESS, HIGHLIGHT_COLOUR,
                      COLOUR_LIST, colour_name, PANEL_BACKGROUND,
                      PANEL_BORDER_COLOUR, STATUS_BACKGROUND, ACCENT_COLOUR,
                      GRID_COLOUR, MUTED_TEXT_COLOUR)

Y_FONT_PADDING = 2


def _print_to_image(text: str, x: int, y: int, font: pygame.font.Font,
                    image: pygame.Surface,
                    colour: tuple[int, int, int] = TEXT_COLOUR) -> None:
    """Use <font> to print <text> to (<x>, <y>) on <image> with <colour>.
    """
    text_surface = font.render(text, True, colour)
    image.blit(text_surface, (x, y))


def _create_vertical_gradient(size: tuple[int, int],
                              start_colour: tuple[int, int, int],
                              end_colour: tuple[int, int, int]) -> pygame.Surface:
    """Return a surface filled with a vertical gradient between two colours."""
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)

    if height <= 1:
        surface.fill(start_colour)
        return surface

    for y in range(height):
        ratio = y / (height - 1)
        colour = tuple(
            int(start_colour[i] + (end_colour[i] - start_colour[i]) * ratio)
            for i in range(3)
        )
        pygame.draw.line(surface, colour, (0, y), (width, y))

    return surface


def _mix_with_white(colour: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Return <colour> lightened by <factor> toward white."""
    factor = max(0.0, min(1.0, factor))
    return tuple(int(colour[i] * factor + 255 * (1 - factor)) for i in range(3))


def _format_key_name(key: int) -> str:
    """Return the display name for a pygame key code."""
    return pygame.key.name(key).upper()


class Renderer:
    """Responsible for drawing the Blocky board, UI chrome, and HUD."""

    _screen: pygame.Surface
    _font: pygame.font.Font
    _title_font: pygame.font.Font
    _small_font: pygame.font.Font
    _icon_font: pygame.font.Font
    _board_size: int
    _sidebar_width: int
    _panel_padding: int
    _scoreboard_height: int
    _board_rect: pygame.Rect
    _sidebar_rect: pygame.Rect
    _scoreboard_rect: pygame.Rect
    _instruction_position: tuple[int, int]
    _status_rect: pygame.Rect
    _status_position: tuple[int, int]
    _board_background: pygame.Surface
    _scoreboard_base: pygame.Surface
    _instruction_surface: pygame.Surface
    _action_icons: dict[str, pygame.Surface]
    _icon_actions: dict[str, Action]
    _default_icon: pygame.Surface
    _muted_text_colour: tuple[int, int, int]
    _score_card_height: int

    def __init__(self, size: int) -> None:
        """Initialize this Renderer for a board with dimensions <size> x <size>.
        """
        self._board_size = size
        pygame.display.set_caption('Blocky: Architect Edition')

        default_font = pygame.font.get_default_font()
        self._font = pygame.font.Font(default_font, 16)
        self._title_font = pygame.font.Font(default_font, 20)
        self._title_font.set_bold(True)
        self._small_font = pygame.font.Font(default_font, 13)
        self._icon_font = pygame.font.Font(default_font, 14)
        self._icon_font.set_bold(True)

        self._muted_text_colour = MUTED_TEXT_COLOUR

        status_height = self._font.get_height() + 24
        self._sidebar_width = 320
        self._panel_padding = 18
        self._score_card_height = 76

        height = size + status_height
        width = size + self._sidebar_width

        self._screen = pygame.display.set_mode((width, height))

        self._board_rect = pygame.Rect(0, 0, size, size)
        self._sidebar_rect = pygame.Rect(size, 0, self._sidebar_width, size)
        available_sidebar_height = self._sidebar_rect.height - 200
        self._scoreboard_height = max(240, min(360, available_sidebar_height))
        self._scoreboard_rect = pygame.Rect(
            self._sidebar_rect.left + self._panel_padding,
            self._sidebar_rect.top + self._panel_padding,
            self._sidebar_width - 2 * self._panel_padding,
            self._scoreboard_height
        )

        instruction_height = max(
            160,
            self._sidebar_rect.height - self._scoreboard_height
            - 3 * self._panel_padding
        )
        instruction_width = self._scoreboard_rect.width
        instruction_y = self._scoreboard_rect.bottom + self._panel_padding
        self._instruction_position = (
            self._scoreboard_rect.left,
            instruction_y
        )

        self._status_rect = pygame.Rect(
            0,
            size,
            width,
            status_height
        )
        self._status_position = (
            self._status_rect.left + 16,
            self._status_rect.top + (self._status_rect.height - self._font.get_height()) // 2
        )

        self._board_background = self._create_board_background()
        self._scoreboard_base = self._create_panel_surface(
            (self._scoreboard_rect.width, self._scoreboard_rect.height)
        )
        self._instruction_surface = self._create_instruction_surface(
            instruction_width, instruction_height
        )

        self._action_icons = {}
        self._icon_actions = {}
        palette = [ACCENT_COLOUR] + COLOUR_LIST
        seen: set[str] = set()
        for index, action in enumerate(KEY_ACTION.values()):
            if action.short_name in seen:
                continue
            seen.add(action.short_name)
            colour = _mix_with_white(palette[index % len(palette)], 0.45)
            self._action_icons[action.short_name] = self._create_action_icon(
                action, colour
            )
            self._icon_actions[action.short_name] = action

        if self._action_icons:
            self._default_icon = next(iter(self._action_icons.values()))
        else:
            self._default_icon = self._create_fallback_icon()

    def _create_board_background(self) -> pygame.Surface:
        surface = _create_vertical_gradient(
            (self._board_size, self._board_size),
            _mix_with_white(PANEL_BACKGROUND, 0.75),
            _mix_with_white(PANEL_BACKGROUND, 0.35)
        )
        grid_colour = _mix_with_white(GRID_COLOUR, 0.4)
        grid_step = max(40, self._board_size // 16)
        for x in range(grid_step, self._board_size, grid_step):
            pygame.draw.line(surface, grid_colour, (x, 0), (x, self._board_size), 1)
        for y in range(grid_step, self._board_size, grid_step):
            pygame.draw.line(surface, grid_colour, (0, y), (self._board_size, y), 1)
        return surface

    def _create_panel_surface(self, size: tuple[int, int]) -> pygame.Surface:
        surface = _create_vertical_gradient(
            size,
            _mix_with_white(PANEL_BACKGROUND, 0.75),
            PANEL_BACKGROUND
        )
        pygame.draw.rect(surface, PANEL_BORDER_COLOUR,
                         surface.get_rect(), width=2, border_radius=12)
        return surface

    def _create_action_icon(self, action: Action,
                            colour: tuple[int, int, int]) -> pygame.Surface:
        surface = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.rect(surface, colour, surface.get_rect(), border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER_COLOUR, surface.get_rect(),
                         width=2, border_radius=10)
        glyph = ''.join(word[0] for word in action.label.split()).upper()
        if len(glyph) > 3:
            glyph = glyph[:3]
        text = self._icon_font.render(glyph, True, TEXT_COLOUR)
        rect = text.get_rect(center=(surface.get_width() // 2,
                                     surface.get_height() // 2))
        surface.blit(text, rect)
        return surface

    def _create_fallback_icon(self) -> pygame.Surface:
        surface = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.rect(surface, _mix_with_white(ACCENT_COLOUR, 0.4),
                         surface.get_rect(), border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER_COLOUR, surface.get_rect(),
                         width=2, border_radius=10)
        text = self._icon_font.render('?', True, TEXT_COLOUR)
        rect = text.get_rect(center=(surface.get_width() // 2,
                                     surface.get_height() // 2))
        surface.blit(text, rect)
        return surface

    def _create_instruction_surface(self, width: int,
                                    height: int) -> pygame.Surface:
        panel = self._create_panel_surface((width, height))
        y = 12

        y = self._draw_section_header(panel, 'Human Controls', y)
        y = self._draw_instruction_line(panel, 'Change depth focus', 'W / S', y)

        for action in self._icon_actions.values():
            y = self._draw_action_instruction(panel, action, y)

        y += 6
        y = self._draw_section_header(panel, 'Computer Assist', y)
        y = self._draw_instruction_line(panel, 'Advance AI turn', 'Left Click', y)

        y += 6
        y = self._draw_section_header(panel, 'Palette', y)
        for colour in COLOUR_LIST:
            y = self._draw_colour_chip(panel, colour, y)

        return panel

    def _draw_section_header(self, surface: pygame.Surface, title: str,
                             y: int) -> int:
        text = self._title_font.render(title, True, ACCENT_COLOUR)
        surface.blit(text, (12, y))
        y += text.get_height() + 4
        pygame.draw.line(surface, _mix_with_white(PANEL_BORDER_COLOUR, 0.6),
                         (12, y), (surface.get_width() - 12, y), 1)
        return y + 8

    def _draw_instruction_line(self, surface: pygame.Surface, description: str,
                               key_label: str, y: int) -> int:
        text = self._font.render(description, True, TEXT_COLOUR)
        surface.blit(text, (12, y))
        key_surface = self._small_font.render(key_label, True,
                                              self._muted_text_colour)
        surface.blit(key_surface, (surface.get_width() - key_surface.get_width() - 12, y))
        return y + text.get_height() + 8

    def _draw_action_instruction(self, surface: pygame.Surface,
                                 action: Action, y: int) -> int:
        icon = self._action_icons[action.short_name]
        surface.blit(icon, (12, y))
        name_surface = self._font.render(action.label, True, TEXT_COLOUR)
        surface.blit(name_surface, (12 + icon.get_width() + 10, y + 4))

        keys = [
            _format_key_name(key)
            for key, candidate in KEY_ACTION.items()
            if candidate.short_name == action.short_name
        ]
        key_surface = self._small_font.render(' / '.join(keys), True,
                                              self._muted_text_colour)
        surface.blit(key_surface, (surface.get_width() - key_surface.get_width() - 12,
                                   y + 8))
        return y + icon.get_height() + 10

    def _draw_colour_chip(self, surface: pygame.Surface,
                          colour: tuple[int, int, int], y: int) -> int:
        chip_rect = pygame.Rect(12, y, 18, 18)
        pygame.draw.rect(surface, colour, chip_rect, border_radius=4)
        pygame.draw.rect(surface, PANEL_BORDER_COLOUR, chip_rect,
                         width=1, border_radius=4)
        label = self._small_font.render(colour_name(colour), True, TEXT_COLOUR)
        surface.blit(label, (chip_rect.right + 8, y + 1))
        return y + chip_rect.height + 6

    def clear(self) -> None:
        """Clear the screen and draw the static UI chrome."""
        self._screen.fill(BACKGROUND_COLOUR)
        self._screen.blit(self._board_background, self._board_rect.topleft)

        pygame.draw.rect(self._screen, PANEL_BACKGROUND, self._sidebar_rect)
        pygame.draw.rect(self._screen, PANEL_BORDER_COLOUR, self._sidebar_rect,
                         width=2)

        self._screen.blit(self._scoreboard_base, self._scoreboard_rect.topleft)
        self._screen.blit(self._instruction_surface, self._instruction_position)

        pygame.draw.rect(self._screen, STATUS_BACKGROUND, self._status_rect)
        pygame.draw.rect(self._screen, PANEL_BORDER_COLOUR, self._status_rect,
                         width=2)

    def draw_image(self, action: Action,
                   pos: tuple[int, int], size: int) -> None:
        """Draw an overlay representing <action> centered on the block."""
        icon = self._action_icons.get(action.short_name, self._default_icon)
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (*ACCENT_COLOUR, 40), overlay.get_rect(),
                         border_radius=12)
        pygame.draw.rect(overlay, ACCENT_COLOUR, overlay.get_rect(),
                         width=3, border_radius=12)

        icon_size = max(24, min(size - 12, 72))
        scaled_icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
        icon_rect = scaled_icon.get_rect(center=(size // 2, size // 2))
        overlay.blit(scaled_icon, icon_rect)
        self._screen.blit(overlay, pos)

    def draw_board(self, squares: list[tuple[tuple[int, int, int],
                                             tuple[int, int], int]]) -> None:
        """Draw each block in <squares> onto the board."""
        self._screen.blit(self._board_background, self._board_rect.topleft)
        for colour, pos, block_size in squares:
            rect = pygame.Rect(pos[0], pos[1], block_size, block_size)
            pygame.draw.rect(self._screen, colour, rect)
            pygame.draw.rect(self._screen, OUTLINE_COLOUR, rect,
                             OUTLINE_THICKNESS)

        pygame.draw.rect(self._screen, PANEL_BORDER_COLOUR, self._board_rect,
                         width=2)

    def highlight_block(self, pos: tuple[int, int], size: int) -> None:
        """Draw a translucent highlight around a block."""
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (*HIGHLIGHT_COLOUR, 64), overlay.get_rect(),
                         border_radius=8)
        pygame.draw.rect(overlay, HIGHLIGHT_COLOUR, overlay.get_rect(),
                         width=3, border_radius=8)
        self._screen.blit(overlay, pos)

    def draw_scoreboard(self, entries: list[dict[str, Any]],
                        highlight_id: int, turn: int | None,
                        max_turns: int | None, *, title: str = 'Match Dashboard',
                        subtitle: str | None = None) -> None:
        """Render the player scoreboard in the sidebar."""
        panel = self._scoreboard_base.copy()

        inner_x = 16
        width = panel.get_width() - 2 * inner_x
        y = 14

        header = self._title_font.render(title, True, ACCENT_COLOUR)
        panel.blit(header, (inner_x, y))
        y += header.get_height() + 4

        if subtitle is None and turn is not None and max_turns is not None:
            subtitle = f'Round {turn + 1} of {max_turns}'
        if subtitle:
            sub_surface = self._small_font.render(subtitle, True,
                                                  self._muted_text_colour)
            panel.blit(sub_surface, (inner_x, y))
            y += sub_surface.get_height() + 8

        if not entries:
            message = self._font.render('No players joined.', True, TEXT_COLOUR)
            panel.blit(message, (inner_x, y))
        else:
            max_raw = max(int(entry['raw_score']) for entry in entries)
            max_raw = max_raw if max_raw > 0 else 1

            for entry in entries:
                if y + self._score_card_height > panel.get_height() - 12:
                    break
                y = self._draw_score_card(panel, entry, highlight_id, y,
                                          inner_x, width, max_raw)

        self._screen.blit(panel, self._scoreboard_rect.topleft)

    def _draw_score_card(self, surface: pygame.Surface, entry: dict[str, Any],
                         highlight_id: int, y: int, x: int, width: int,
                         max_raw: int) -> int:
        rect = pygame.Rect(x, y, width, self._score_card_height)
        goal_colour = cast(tuple[int, int, int], entry['goal_colour'])
        fill_colour = _mix_with_white(goal_colour, 0.82)
        pygame.draw.rect(surface, fill_colour, rect, border_radius=12)
        border_colour = (goal_colour if int(entry['id']) == highlight_id
                         else _mix_with_white(goal_colour, 0.6))
        pygame.draw.rect(surface, border_colour, rect, width=2, border_radius=12)

        title_text = self._font.render(
            f"P{int(entry['id'])} · {entry['type']}", True, TEXT_COLOUR
        )
        surface.blit(title_text, (rect.x + 12, rect.y + 8))

        goal_text = self._small_font.render(
            str(entry['goal']), True, self._muted_text_colour
        )
        surface.blit(goal_text, (rect.x + 12, rect.y + 8 + title_text.get_height()))

        net_score = int(entry['net_score'])
        net_colour = ACCENT_COLOUR if int(entry['id']) == highlight_id else TEXT_COLOUR
        net_text = self._font.render(f'{net_score:,}', True, net_colour)
        surface.blit(net_text, (rect.right - net_text.get_width() - 12,
                                rect.y + 8))

        raw = int(entry['raw_score'])
        penalty = int(entry['penalty'])
        detail = self._small_font.render(
            f'{raw:,} - {penalty}', True, self._muted_text_colour
        )
        surface.blit(detail, (rect.right - detail.get_width() - 12,
                               rect.y + 8 + net_text.get_height()))

        bar_rect = pygame.Rect(rect.x + 12,
                               rect.bottom - 16,
                               rect.width - 24,
                               8)
        pygame.draw.rect(surface, _mix_with_white(goal_colour, 0.65),
                         bar_rect, border_radius=4)
        fill_width = int((raw / max_raw) * bar_rect.width)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width,
                                    bar_rect.height)
            pygame.draw.rect(surface, goal_colour, fill_rect, border_radius=4)

        return rect.bottom + 10

    def text_height(self) -> int:
        """Return the height between lines of text in pixels."""
        return self._font.get_height() + Y_FONT_PADDING

    def print(self, text: str, x: int, y: int) -> None:
        """Print <text> to the (<x>, <y>) location on the screen."""
        _print_to_image(text, x, y, self._font, self._screen)

    def draw_status(self, message: str) -> None:
        """Draw the current status of the game."""
        pygame.draw.rect(self._screen, STATUS_BACKGROUND, self._status_rect)
        pygame.draw.rect(self._screen, PANEL_BORDER_COLOUR, self._status_rect,
                         width=2)
        surface = self._font.render(message, True, TEXT_COLOUR)
        self._screen.blit(surface, self._status_position)

    def save_to_file(self, filename: str) -> None:
        """Save the current graphics on the screen to a file named <filename>."""
        pygame.image.save(self._screen, filename)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': [],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'settings',
            'pygame'
        ],
        'max-args': 6,
        'generated-members': 'pygame.*'
    })
