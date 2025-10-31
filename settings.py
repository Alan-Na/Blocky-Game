# Colours that we could use in the game
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PACIFIC_POINT = (1, 128, 181)
OLD_OLIVE = (138, 151, 71)
REAL_RED = (199, 44, 58)
MELON_MAMBO = (234, 62, 112)
DAFFODIL_DELIGHT = (255, 211, 92)
TEMPTING_TURQUOISE = (75, 196, 213)

# A palette of the colours we use in the game
COLOUR_LIST = [PACIFIC_POINT, REAL_RED, OLD_OLIVE, DAFFODIL_DELIGHT]

# The game board will be a square with this size.
BOARD_SIZE = 800

# The background will be this colour.
# Core theme colours for the in-game renderer.
BACKGROUND_COLOUR = BLACK
# Text will have this colour.
TEXT_COLOUR = WHITE
# Blocks will have this colour outline.
OUTLINE_COLOUR = BLACK
# Blocks will have this thick of an outline.
OUTLINE_THICKNESS = 2
# Blocks will be highlighted with this colour.
HIGHLIGHT_COLOUR = TEMPTING_TURQUOISE
# Highlighted blocks will have this thickness to the highlight.
HIGHLIGHT_THICKNESS = 5

# Extended palette used by the upgraded interface elements.
PANEL_BACKGROUND = (17, 21, 31)
PANEL_BORDER_COLOUR = (66, 90, 120)
STATUS_BACKGROUND = (12, 16, 24)
ACCENT_COLOUR = TEMPTING_TURQUOISE
GRID_COLOUR = (32, 38, 54)
MUTED_TEXT_COLOUR = (178, 188, 205)

# The number of seconds a move is animated for.
ANIMATION_DURATION = 1


class UnknownColourError(Exception):
    """ An exception to be raised when the name of the colour is not known.
    """
    pass


def colour_name(colour: tuple[int, int, int]) -> str:
    """Return the colour name associated with this colour value, or
    the empty string if this colour value isn't in our colour list.

    Raise an UnknownColourError if the name of the colour is not known.
    """
    colour_names = {
        PACIFIC_POINT: 'Pacific Point',
        REAL_RED: 'Real Red',
        OLD_OLIVE: 'Old Olive',
        DAFFODIL_DELIGHT: 'Daffodil Delight'
    }

    if colour in colour_names:
        return colour_names[colour]
    else:
        raise UnknownColourError
