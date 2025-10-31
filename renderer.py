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
    _instruction_font: pygame.font.Font
    _score_font: pygame.font.Font
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
    _instruction_background: pygame.Surface
    _instruction_content: pygame.Surface
    _instruction_size: tuple[int, int]
    _instruction_scroll: int
    _exit_button_rect: pygame.Rect
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
        self._instruction_font = pygame.font.Font(default_font, 18)
        self._score_font = pygame.font.Font(default_font, 30)
        self._score_font.set_bold(True)
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

        self._board_background = self._create_board_background()
        self._scoreboard_base = self._create_panel_surface(
            (self._scoreboard_rect.width, self._scoreboard_rect.height)
        )
        self._instruction_size = (instruction_width, instruction_height)
        self._instruction_background = self._create_panel_surface(self._instruction_size)
        self._instruction_content = self._create_instruction_content(
            self._instruction_size[0] - 32
        )
        self._instruction_scroll = 0
        self._exit_button_rect = pygame.Rect(0, 0, 0, 0)

    def layout(self) -> dict[str, pygame.Rect]:
        """Return copies of key layout rectangles for external use."""
        return {
            'screen': self._screen.get_rect().copy(),
            'board': self._board_rect.copy(),
            'sidebar': self._sidebar_rect.copy(),
            'status': self._status_rect.copy()
        }

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

    def _create_instruction_content(self, width: int) -> pygame.Surface:
        temp_height = 2000
        surface = pygame.Surface((width, temp_height), pygame.SRCALPHA)
        y = 0

        y = self._draw_section_header(surface, 'Human Controls', y)
        y = self._draw_instruction_line(surface, 'Change depth focus', 'W / S', y)

        for action in self._icon_actions.values():
            y = self._draw_action_instruction(surface, action, y)

        y += 6
        y = self._draw_section_header(surface, 'Computer Assist', y)
        y = self._draw_instruction_line(surface, 'Advance AI turn', 'Left Click', y)

        y += 6
        y = self._draw_section_header(surface, 'Palette', y)
        for colour in COLOUR_LIST:
            y = self._draw_colour_chip(surface, colour, y)

        content_height = max(1, min(y, temp_height))
        trimmed = pygame.Surface((width, content_height), pygame.SRCALPHA)
        trimmed.blit(surface, (0, 0))
        return trimmed

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

    def clear_menu(self) -> None:
        """Clear the screen for menu-style interfaces."""
        self._screen.fill(BACKGROUND_COLOUR)
        overlay = _create_vertical_gradient(
            self._screen.get_size(),
            _mix_with_white(PANEL_BACKGROUND, 0.65),
            _mix_with_white(PANEL_BACKGROUND, 0.35)
        )
        self._screen.blit(overlay, (0, 0))

    def draw_menu(self, title: str, subtitle: str | None,
                  options: list[str], hovered: str | None = None) -> dict[str, pygame.Rect]:
        """Draw a simple centered menu.

        Return a mapping of option labels to their screen rects.
        """
        self.clear_menu()
        screen_rect = self._screen.get_rect()
        button_height = 56
        spacing = 18
        panel_width = min(480, screen_rect.width - 160)
        panel_height = max(
            260,
            140 + len(options) * (button_height + spacing)
        )

        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = screen_rect.center

        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, _mix_with_white(PANEL_BACKGROUND, 0.8),
                         panel.get_rect(), border_radius=20)
        pygame.draw.rect(panel, PANEL_BORDER_COLOUR, panel.get_rect(),
                         width=2, border_radius=20)

        y = 28
        header = self._title_font.render(title, True, ACCENT_COLOUR)
        header_rect = header.get_rect(centerx=panel_rect.width // 2, y=y)
        panel.blit(header, header_rect)
        y = header_rect.bottom + 6

        if subtitle:
            sub_surface = self._small_font.render(subtitle, True,
                                                  self._muted_text_colour)
            sub_rect = sub_surface.get_rect(centerx=panel_rect.width // 2, y=y)
            panel.blit(sub_surface, sub_rect)
            y = sub_rect.bottom + 18
        else:
            y += 12

        button_width = panel_rect.width - 80
        button_rects: dict[str, pygame.Rect] = {}
        for label in options:
            button_rect = pygame.Rect(40, y, button_width, button_height)
            is_hovered = hovered == label
            fill_colour = _mix_with_white(ACCENT_COLOUR, 0.82 if is_hovered else 0.9)
            pygame.draw.rect(panel, fill_colour, button_rect, border_radius=12)
            pygame.draw.rect(panel, ACCENT_COLOUR, button_rect,
                             width=3 if is_hovered else 2, border_radius=12)

            text_surface = self._font.render(label, True, TEXT_COLOUR)
            text_rect = text_surface.get_rect(center=button_rect.center)
            panel.blit(text_surface, text_rect)

            button_rects[label] = button_rect.move(panel_rect.left,
                                                   panel_rect.top)
            y += button_height + spacing

        self._screen.blit(panel, panel_rect.topleft)
        return button_rects

    def draw_instruction_screen(self, title: str, lines: list[str],
                                button_label: str, hovered: bool,
                                scroll_offset: int,
                                footer: str | None = None) -> tuple[pygame.Rect, int, int]:
        """Draw an instruction panel.

        Return a tuple containing the back button rect, the maximum scroll value,
        and the clamped scroll offset that was applied during rendering.
        """
        self.clear_menu()
        screen_rect = self._screen.get_rect()
        line_height = self._instruction_font.get_height() + 8
        panel_width = min(620, screen_rect.width - 160)
        panel_height = min(max(360, screen_rect.height - 220),
                           screen_rect.height - 120)

        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.centerx = screen_rect.centerx
        panel_rect.top = max(60, (screen_rect.height - panel_height) // 2 - 40)

        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, _mix_with_white(PANEL_BACKGROUND, 0.78),
                         panel.get_rect(), border_radius=18)
        pygame.draw.rect(panel, PANEL_BORDER_COLOUR, panel.get_rect(),
                         width=2, border_radius=18)

        y = 26
        header = self._title_font.render(title, True, ACCENT_COLOUR)
        header_rect = header.get_rect(centerx=panel_rect.width // 2, y=y)
        panel.blit(header, header_rect)
        y = header_rect.bottom + 16

        content_width = panel_rect.width - 64
        entries: list[tuple[pygame.Surface, int]] = []
        cursor = 0
        for line in lines:
            if line.strip() == '':
                cursor += line_height // 2
                continue
            text_surface = self._instruction_font.render(line, True, TEXT_COLOUR)
            entries.append((text_surface, cursor))
            cursor += line_height

        content_height = max(line_height, cursor)
        content_surface = pygame.Surface((content_width, content_height), pygame.SRCALPHA)
        for surface, pos in entries:
            content_surface.blit(surface, (0, pos))

        viewport_height = panel_rect.height - y - 80
        viewport_height = max(140, viewport_height)
        viewport_height = min(content_height, viewport_height)
        max_scroll = max(0, content_height - viewport_height)
        scroll_offset = max(0, min(scroll_offset, max_scroll))

        # Draw background for content area
        content_bg_rect = pygame.Rect(24, y - 8, panel_rect.width - 48, viewport_height + 16)
        pygame.draw.rect(panel, _mix_with_white(PANEL_BACKGROUND, 0.68),
                         content_bg_rect, border_radius=12)
        pygame.draw.rect(panel, _mix_with_white(PANEL_BORDER_COLOUR, 0.8),
                         content_bg_rect, width=1, border_radius=12)

        view_area = pygame.Rect(0, scroll_offset, content_width, viewport_height)
        panel.blit(content_surface, (32, y), view_area)

        # Draw simple scroll indicator if needed
        if max_scroll > 0 and viewport_height > 0:
            track_rect = pygame.Rect(panel_rect.width - 28, y, 8, viewport_height)
            pygame.draw.rect(panel, _mix_with_white(PANEL_BORDER_COLOUR, 0.55),
                             track_rect, border_radius=4)
            thumb_height = max(28, int((viewport_height / content_height) * track_rect.height))
            thumb_range = track_rect.height - thumb_height
            if thumb_range < 1:
                thumb_range = 1
            thumb_offset = int((scroll_offset / max_scroll) * thumb_range) if max_scroll else 0
            thumb_rect = pygame.Rect(track_rect.x, track_rect.y + thumb_offset,
                                     track_rect.width, thumb_height)
            pygame.draw.rect(panel, ACCENT_COLOUR, thumb_rect, border_radius=4)

        self._screen.blit(panel, panel_rect.topleft)

        if footer:
            footer_surface = self._small_font.render(footer, True,
                                                     self._muted_text_colour)
            footer_rect = footer_surface.get_rect(centerx=screen_rect.centerx,
                                                  y=panel_rect.bottom + 16)
            self._screen.blit(footer_surface, footer_rect)

        button_width = 160
        button_height = 50
        button_rect = pygame.Rect(0, 0, button_width, button_height)
        button_rect.centerx = screen_rect.centerx
        button_rect.top = panel_rect.bottom + 40

        fill_colour = _mix_with_white(ACCENT_COLOUR, 0.8 if hovered else 0.9)
        pygame.draw.rect(self._screen, fill_colour, button_rect,
                         border_radius=12)
        pygame.draw.rect(self._screen, ACCENT_COLOUR, button_rect,
                         width=3 if hovered else 2, border_radius=12)

        label_surface = self._font.render(button_label, True, TEXT_COLOUR)
        label_rect = label_surface.get_rect(center=button_rect.center)
        self._screen.blit(label_surface, label_rect)

        return button_rect, max_scroll, scroll_offset

    def draw_overlay_scoreboard(self, entries: list[dict[str, Any]],
                                highlight_id: int) -> None:
        """Compatibility shim for legacy overlay scoreboard calls."""
        if not entries:
            return

        formatted: list[dict[str, Any]] = []
        for entry in entries:
            score = entry.get('score')
            if score is None:
                goal_score = int(entry.get('goal_score', 0))
                penalty = int(entry.get('penalty', 0))
                score = goal_score - penalty
            formatted.append({
                'id': entry.get('id', 0),
                'score': score,
                'goal_colour': entry.get('goal_colour')
            })

        self.draw_scoreboard(formatted, highlight_id)


    def draw_instruction_panel(self) -> None:
        panel = self._instruction_background.copy()
        margin = 16
        viewport_height = panel.get_height() - 2 * margin
        viewport_width = panel.get_width() - 2 * margin

        content = self._instruction_content
        content_height = content.get_height()
        max_scroll = max(0, content_height - viewport_height)
        self._instruction_scroll = max(0, min(self._instruction_scroll, max_scroll))

        view_rect = pygame.Rect(0, self._instruction_scroll,
                                content.get_width(), viewport_height)
        panel.blit(content, (margin, margin), view_rect)

        if max_scroll > 0 and viewport_height > 0:
            track_height = viewport_height
            track_rect = pygame.Rect(panel.get_width() - margin - 6,
                                     margin, 6, track_height)
            pygame.draw.rect(panel, _mix_with_white(PANEL_BORDER_COLOUR, 0.5),
                             track_rect, border_radius=3)

            thumb_height = max(24, int(track_height * (viewport_height / content_height)))
            thumb_range = track_height - thumb_height
            thumb_offset = int((self._instruction_scroll / max_scroll) * thumb_range) if max_scroll else 0
            thumb_rect = pygame.Rect(track_rect.x,
                                     track_rect.y + thumb_offset,
                                     track_rect.width,
                                     thumb_height)
            pygame.draw.rect(panel, ACCENT_COLOUR, thumb_rect, border_radius=3)

        self._screen.blit(panel, self._instruction_position)

    def scroll_instruction(self, delta: int) -> None:
        if delta == 0:
            return
        viewport_height = self._instruction_size[1] - 32
        max_scroll = max(0, self._instruction_content.get_height() - viewport_height)
        self._instruction_scroll = max(0, min(self._instruction_scroll + delta, max_scroll))

    def instruction_rect(self) -> pygame.Rect:
        return pygame.Rect(self._instruction_position,
                           self._instruction_size)

    def exit_button_rect(self) -> pygame.Rect:
        return self._exit_button_rect.copy()

    def reset_exit_button(self) -> None:
        self._exit_button_rect = pygame.Rect(0, 0, 0, 0)

    def clear(self) -> None:
        """Clear the screen and draw the static UI chrome."""
        self._screen.fill(BACKGROUND_COLOUR)
        self._screen.blit(self._board_background, self._board_rect.topleft)

        pygame.draw.rect(self._screen, PANEL_BACKGROUND, self._sidebar_rect)
        pygame.draw.rect(self._screen, PANEL_BORDER_COLOUR, self._sidebar_rect,
                         width=2)

        self._screen.blit(self._scoreboard_base, self._scoreboard_rect.topleft)
        self._screen.blit(self._instruction_background, self._instruction_position)

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
                        highlight_id: int) -> None:
        """Render a compact scoreboard in the sidebar."""
        panel = self._scoreboard_base.copy()
        self._exit_button_rect = pygame.Rect(0, 0, 0, 0)

        if not entries:
            self._screen.blit(panel, self._scoreboard_rect.topleft)
            return

        button_width = 120
        button_height = 34
        button_rect = pygame.Rect(panel.get_width() - button_width - 14,
                                  12, button_width, button_height)
        pygame.draw.rect(panel, _mix_with_white(ACCENT_COLOUR, 0.75),
                         button_rect, border_radius=10)
        pygame.draw.rect(panel, ACCENT_COLOUR, button_rect,
                         width=2, border_radius=10)
        exit_text = self._font.render('Exit', True, TEXT_COLOUR)
        text_rect = exit_text.get_rect(center=button_rect.center)
        panel.blit(exit_text, text_rect)

        y = button_rect.bottom + 16
        row_height = self._score_font.get_height() + 14
        sorted_entries = sorted(entries, key=lambda item: item['score'], reverse=True)

        for entry in sorted_entries:
            if y + row_height > panel.get_height() - 12:
                break

            pid = int(entry['id'])
            score = int(entry['score'])
            colour = entry.get('goal_colour')
            highlight = pid == highlight_id

            row_rect = pygame.Rect(12, y - 6,
                                   panel.get_width() - 24,
                                   row_height)
            if highlight:
                pygame.draw.rect(panel, _mix_with_white(ACCENT_COLOUR, 0.85),
                                 row_rect, border_radius=12)

            name_colour = ACCENT_COLOUR if highlight else self._muted_text_colour
            label_text = self._small_font.render(f'P{pid}', True, name_colour)
            label_x = row_rect.x + 12

            if colour is not None:
                pygame.draw.circle(panel, colour, (label_x, row_rect.centery), 6)
                pygame.draw.circle(panel, PANEL_BORDER_COLOUR,
                                   (label_x, row_rect.centery), 6, width=1)
                label_x += 14

            panel.blit(label_text, (label_x, y))

            score_colour = ACCENT_COLOUR if highlight else TEXT_COLOUR
            score_text = self._score_font.render(f'{score:+}', True, score_colour)
            panel.blit(score_text, (row_rect.right - score_text.get_width() - 14, y - 6))

            y += row_height

        self._screen.blit(panel, self._scoreboard_rect.topleft)
        self._exit_button_rect = button_rect.move(self._scoreboard_rect.left,
                                                  self._scoreboard_rect.top)

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
