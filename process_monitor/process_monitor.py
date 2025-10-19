"""Process Monitor - Qt6 entry point."""

import sys

from PyQt6 import QtWidgets

from process_monitor_gui import ProcessMonitor


def main() -> int:
    """Main entry point for the Process Monitor application."""
    app = QtWidgets.QApplication(sys.argv)
    window = ProcessMonitor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
