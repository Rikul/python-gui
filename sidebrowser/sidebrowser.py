"""Entry point for the PySide6-based browser application."""

import sys

from PySide6.QtWidgets import QApplication

from browser import Browser


def main() -> int:
    """Launch the browser application."""

    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
