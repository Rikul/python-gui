# Tkinter Minesweeper

This is a simple Minesweeper clone built with the Python standard library's `tkinter` toolkit.

## Features
- 10x10 grid with 10 hidden mines placed randomly each game
- Recursive reveal of adjacent tiles when an empty space is uncovered
- Visual icons: 💣 for mines and 🚩 for flags
- Right-click to toggle flags without accidentally revealing tiles
- Menu bar with options to start a new game or exit the application

## Requirements
- Python 3.8+
- Tkinter (bundled with most Python installations; on some Linux distributions you may need to install the `python3-tk` package)

To install Tkinter via `pip`, you can use the `tk` package:

```bash
pip install -r requirements.txt
```

## Running the game

```bash
python tkMinesweeper.py
```

Use left-click to reveal tiles and right-click to toggle flags. Revealing a mine ends the game and automatically starts a new one after a brief pause.
