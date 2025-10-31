# Minesweeper

This folder contains two implementations of the classic Minesweeper game:
- `tkMinesweeper.py` - Built with Python's standard library `tkinter` toolkit
- `qtMinesweeper.py` - Built with `PySide6` (Qt for Python)

## Requirements
- Python 3.8+
- For tkMinesweeper: Tkinter (bundled with most Python installations; on some Linux distributions you may need to install the `python3-tk` package)
- For qtMinesweeper: PySide6

To install all dependencies via `pip`:

```bash
pip install -r requirements.txt
```

## Running the games

### Tkinter version:
```bash
python tkMinesweeper.py
```

### PySide6 version:
```bash
python qtMinesweeper.py
```

Both versions support left-click to reveal tiles and right-click to toggle flags. Revealing a mine ends the game and automatically starts a new one after a brief pause.
