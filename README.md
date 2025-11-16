# Python GUI Projects

This repository contains a collection of simple GUI applications built with Python.

## Installation

To run these applications, it's recommended to use a virtual environment. You can create one using `venv` and install the required packages using `uv` or `pip`.

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows
.venv\Scripts\activate
# On macOS and Linux
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
# or
pip install -r requirements.txt
```

## Applications

### Breakout

A simple Breakout clone built with Pygame.

**To run:**

```bash
python breakout/breakout.py
```

### Minesweeper

A simple Minesweeper clone built with tkinter.

**To run:**

```bash
python minesweeper/tkMinesweeper.py
```

### Note Editor

A simple notepad-like application built with tkinter.

**To run:**

```bash
python note_editor/note_editor.py
```

### Pong

A single-player Pong game built with Pygame.

**To run:**

```bash
python pong/pong.py
```

### qtJSONlint

A JSON formatter and validator built with PySide6. This application allows you to paste or open JSON files, format them in regular or compact mode, customize formatting options, and see detailed error messages for invalid JSON.

**Features:**
- Paste JSON directly or open from a file
- Format in regular (indented) or compact mode
- Customize indent size (0-10 spaces)
- Sort keys alphabetically
- Ensure ASCII output option
- Display detailed parsing errors with line and column numbers
- Save formatted output to a file

**To run:**

```bash
python qtJSONlint/qtJSONlint.py
```

### Process Monitor

A real-time system process monitor with CPU and memory usage graphs built with Python and Qt 6.

**To run:**

```bash
python process_monitor/process_monitor.py
```

### Speed Test

A comprehensive internet speed test application built with Python and tkinter.

**To run:**

```bash
python speed_test/speed_test.py
```

### Star Screensaver

A starfield screensaver simulation built with Pygame.

**To run:**

```bash
python star_screensaver/star_screensaver.py
```

### Tic-Tac-Toe

A simple Tic-Tac-Toe game built with Pygame.

**To run:**

```bash
python tictactoe/tictactoe.py
```

### Web Browser

A simple web browser built with Python and PyQt6.

**To run:**

```bash
python webbrowser/webbrowser.py
```
