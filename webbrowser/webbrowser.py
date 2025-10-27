import sys
from PyQt6.QtWidgets import QApplication
from browser import Browser


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec())
