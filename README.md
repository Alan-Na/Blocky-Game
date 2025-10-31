# Blocky Game

Blocky is a recursive tiling puzzle played on a square board that is broken
into a tree of coloured blocks. Each turn players transform the board to
improve their standing against a randomly assigned scoring goal.

## Gameplay overview
- **Board generation:** A new game starts with a root block that recursively
  smashes into four children until it reaches the requested `max_depth`, giving
  every leaf a position, size, and colour drawn from the palette in
  `settings.py`.【F:block.py†L31-L65】【F:settings.py†L1-L77】
- **Turns:** The main loop hands control to each player in sequence. Players
  submit a move consisting of an action and the block it targets; successful
  actions add their penalty cost before the next player begins their turn.【F:state.py†L70-L144】
- **Goals and scoring:** Every player receives either a `PerimeterGoal` or a
  `BlobGoal`, each bound to a unique colour. Perimeter goals count matching
  tiles along the edge (with corners twice) while blob goals reward the size of
  the largest connected region of the target colour.【F:goal.py†L21-L126】
- **Game end:** After the configured number of rounds the game enters the
  `GameOverState`, tallies each player’s goal score minus penalties, and
  declares the winner.【F:state.py†L146-L287】

## Interface upgrades
- **Neo-noir HUD:** The renderer now builds a neon-inspired layout with a shaded
  board background, chrome panels, and adaptive typography so the game feels at
  home in a portfolio screenshot.【F:renderer.py†L107-L205】
- **Live analytics:** A sidebar scoreboard highlights each player's goal, raw
  score, penalties, and net score, updating every frame and animating the active
  player during turn previews.【F:renderer.py†L367-L452】【F:state.py†L160-L227】
- **Final showcase:** When the game ends the renderer freezes the last board,
  draws the final standings card, and surfaces the winner for a polished wrap
  up.【F:state.py†L298-L348】

## Installation
1. Ensure you are using Python 3.11 or later.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   The game uses `pygame` for rendering and input; it is the only third-party
   requirement.【F:game.py†L1-L83】【F:actions.py†L20-L98】

## Running the game
1. Initialise pygame and launch one of the helper configurations:
   ```bash
   python -m game
   ```
2. Inside `game.py` you can choose from ready-made setups such as
   `create_sample_game()` (human + random + smart), `create_two_player_game()`,
   and more, or construct a `Game` directly by specifying the number of human,
   random, and smart players along with their difficulty levels.【F:game.py†L1-L83】
3. The main loop keeps running until the selected number of turns completes or
   the window is closed.【F:game.py†L44-L83】

## Controls
Human players interact through the keyboard and mouse. The mouse cursor selects
blocks; the `W` and `S` keys move up and down the block tree to change the
selection depth.【F:player.py†L68-L126】

| Key | Action |
| --- | ------ |
| `D` | Rotate the selected block clockwise |
| `A` | Rotate the selected block counter-clockwise |
| `Q` | Swap the block’s children horizontally |
| `E` | Swap the block’s children vertically |
| `SPACE` | Smash the block into four new children (if allowed) |
| `C` | Combine four uniform children back into their parent |
| `R` | Paint the block with your goal colour |
| `TAB` | Pass the turn without acting |

All actions (except pass) charge the penalty associated with the `Action`
object defined in `actions.py`.【F:actions.py†L100-L158】

## Player types
- **HumanPlayer:** Listens for keyboard events, allowing a person to pick any
  block and trigger the desired action.【F:player.py†L68-L126】
- **RandomPlayer:** Waits for a mouse click, then chooses uniformly from the set
  of valid moves discovered by simulating each action on copies of the board; it
  passes only if no other move works.【F:player.py†L133-L187】
- **SmartPlayer:** Samples up to `difficulty` valid moves, scores each simulated
  outcome using its goal, and executes the highest-scoring option; otherwise it
  passes.【F:player.py†L189-L250】

## Working with the codebase
- Blocks form a quadtree. Helpers such as `_block_to_squares`, `child_size`,
  `rotate`, `swap`, `smash`, `combine`, and `create_copy` encapsulate the core
  transformations used by the renderer and players.【F:block.py†L31-L347】
- The renderer converts a board into drawable squares via
  `_block_to_squares`, renders the neon HUD, and manages the scoreboard panels
  that drive both in-game and end-game overlays.【F:renderer.py†L313-L452】
- Goals rely on `flatten`, which expands the quadtree into a grid of unit cell
  colours for scoring calculations and AI lookahead.【F:goal.py†L43-L126】

## Testing
Automated tests rely on pygame; if it is not installed, `pytest example_tests.py`
will fail during import. Once pygame is available you can run:
```bash
pytest example_tests.py
pytest a2_test.py
```
These suites exercise the tree operations, goal logic, and player behaviours
implemented in the modules above.【F:goal.py†L21-L126】【F:player.py†L1-L250】
