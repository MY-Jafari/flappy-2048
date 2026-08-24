# Flappy 2048

A 2D arcade game that mixes **Flappy Bird** mechanics with **2048** scoring:
hop a numbered cube through the gaps of scrolling columns, merge equal
numbers (2+2=4) by touching the number badge, and reach **2048** to win.

Built with **pygame-ce** (the actively maintained community edition of
pygame) and designed so the core game logic is completely independent of
pygame — ready to be ported to HTML5/JavaScript later.

## Requirements

- Python 3.10+
- `pygame-ce` (see `requirements.txt`)

```bash
pip install -r requirements.txt
```

## How to run

```bash
python main.py
```

## How to play

- **Jump:** click / tap / Space (also works with ↑ and W). Works on
  touch screens — no keyboard needed.
- **Goal:** fly through the gaps. When your cube touches the **number
  badge** in the middle of a gap, the badge's number merges with yours if
  they are equal (2+2=4, 4+4=8, ...). Your cube's color and number update
  with each merge.
- **Watch out:** touching the solid column body, or leaving the top or
  bottom of the screen, ends the run.
- **Win:** reach **2048** and enjoy the confetti.
- **Quit:** Esc or Q.

The best score (the biggest number your cube ever reached) is saved in
`best_score.json` and survives restarts. Difficulty increases over time —
columns scroll faster and faster, while the gap size stays fair.

## Project structure

The code is split so that **logic** and **rendering** are cleanly
separated. Everything in the logic layer is plain Python (no pygame) and
can be ported to JavaScript almost line-for-line.

| File | Layer | Purpose |
| --- | --- | --- |
| `main.py` | app | Entry point, game loop, state machine (Start / Playing / GameOver / Win) and event handling |
| `settings.py` | config | All tunable values: window size, physics, colors, difficulty — no pygame imports |
| `game_logic.py` | **logic** | 2048 merging, column number generation, gradual difficulty, collision helpers — pure functions |
| `player.py` | **logic** | Player cube: physics (gravity/jump), current number, merge pulse — no pygame |
| `obstacle.py` | **logic** | Columns: gap, number badge, movement, collision tests — no pygame |
| `storage.py` | **logic** | Best-score persistence to JSON — no pygame |
| `ui.py` | render | Everything drawn on screen: cube, columns, clouds, confetti, HUD, screens |
| `sound.py` | render | Synthesized sound effects (no audio asset files) |

Animations are driven by **delta time** (`clock.tick(FPS)`), so the game
runs at the same speed on any machine.

## Tests

```bash
# Pure logic unit tests (no display needed)
python -m unittest tests.test_logic tests.test_smoke

# Headless smoke run (~20s of simulated gameplay, no window)
python main.py --selftest
```

## Porting to the web later

To port to HTML5, rewrite `ui.py` (and the small event loop in `main.py`)
against the Canvas API. The classes in `game_logic.py`, `player.py` and
`obstacle.py` translate directly — they use plain numbers, tuples and
pure functions only.
