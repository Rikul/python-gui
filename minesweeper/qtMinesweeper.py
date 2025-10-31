import sys
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QRadioButton,
    QLabel, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction


class Minesweeper(QMainWindow):
    def __init__(self, grid_size=15, num_mines=25):
        super().__init__()
        self.grid_size = grid_size
        self.num_mines = num_mines
        self.tile_color = "#D3D3D3"  # lightgrey
        
        self.setWindowTitle(f"qtMinesweeper - {self.grid_size}x{self.grid_size}")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        # Emoji icons for mines and flags
        self.mine_icon = "💥"
        self.flag_icon = "🚩"
        
        # Create the menu bar
        self.create_menu_bar()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create the grid layout
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        central_widget.setLayout(self.grid_layout)
        
        self.buttons = []
        self.mines = set()
        self.flags = set()
        self.create_grid()
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # Game menu
        game_menu = menu_bar.addMenu("Game")
        
        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self.new_game)
        game_menu.addAction(new_game_action)
        
        options_action = QAction("Options", self)
        options_action.triggered.connect(self.show_options)
        game_menu.addAction(options_action)
        
        game_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_grid(self):
        """Create a grid of buttons for the game board."""
        button_width = 40
        button_height = 40
        if self.grid_size != 15:
            button_width = 30
            button_height = 30
            
        for row in range(self.grid_size):
            button_row = []
            for col in range(self.grid_size):
                button_font = QFont("Arial", 12, QFont.Bold)
                button = QPushButton()
                button.setFont(button_font)
                button.setStyleSheet(f"background-color: {self.tile_color};")
                button.setFixedSize(button_width, button_height)
                
                # Use lambda with default arguments to capture current row and col
                button.clicked.connect(lambda checked, r=row, c=col: self.on_left_click(r, c))
                button.setContextMenuPolicy(Qt.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda pos, r=row, c=col: self.on_right_click(r, c)
                )
                
                self.grid_layout.addWidget(button, row, col)
                button_row.append(button)
                
            self.buttons.append(button_row)
            
        self.place_mines()
        
        # Adjust window size to fit content
        self.adjustSize()
        self.setFixedSize(self.size())
        
        # Center the window
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def place_mines(self):
        """Create a set of random mine positions on the grid."""
        self.mines = set(random.sample(range(self.grid_size * self.grid_size), self.num_mines))
        
    def count_adjacent_mines(self, row, col):
        """Count the number of mines around a given position."""
        count = 0
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                    if (r * self.grid_size + c) in self.mines:
                        count += 1
        return count
        
    def reveal_tile(self, row, col):
        """Reveal the tile and its adjacent tiles if it has 0 adjacent mines."""
        if row < 0 or row >= self.grid_size or col < 0 or col >= self.grid_size:
            return  # Out of bounds
            
        button = self.buttons[row][col]
        
        if (row, col) in self.flags:
            return
            
        if not button.isEnabled():
            return  # Already revealed
            
        count = self.count_adjacent_mines(row, col)
        button.setEnabled(False)
        button.setStyleSheet("background-color: white;")
        
        if count > 0:
            button.setText(str(count))
        else:
            # Recursively reveal adjacent tiles if the count is 0
            for r in range(row - 1, row + 2):
                for c in range(col - 1, col + 2):
                    self.reveal_tile(r, c)
                    
    def on_left_click(self, row, col):
        """Handle the left-click event."""
        index = row * self.grid_size + col
        
        if (row, col) in self.flags:
            return
            
        if index in self.mines:
            self.show_mine()
            QMessageBox.information(self, "Game Over", "You clicked on a mine!")
            self.new_game()
        else:
            self.reveal_tile(row, col)
            
    def on_right_click(self, row, col):
        """Handle the right-click event to mark a button."""
        button = self.buttons[row][col]
        
        if not button.isEnabled() and button.text() != self.flag_icon:
            return
            
        if (row, col) in self.flags:
            self.flags.remove((row, col))
            if not button.isEnabled():
                return
            button.setText('')
            button.setStyleSheet(f"background-color: {self.tile_color};")
        else:
            if not button.isEnabled():
                return
            self.flags.add((row, col))
            button.setText(self.flag_icon)
            button.setStyleSheet("background-color: lightyellow;")
            
    def show_mine(self):
        """Reveal all tiles on the board and disable all buttons."""
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                btn = self.buttons[row][col]
                index = row * self.grid_size + col
                
                if index in self.mines:
                    btn.setText(self.mine_icon)
                    btn.setStyleSheet("background-color: lightyellow;")
                    btn.setEnabled(False)
                else:
                    count = self.count_adjacent_mines(row, col)
                    btn.setText(str(count) if count > 0 else '')
                    btn.setStyleSheet("background-color: white;")
                    btn.setEnabled(False)
                    
    def new_game(self):
        """Start a new game by resetting the board and placing new mines."""
        self.mines.clear()
        self.flags.clear()
        
        for row in self.buttons:
            for button in row:
                button.setText('')
                button.setStyleSheet(f"background-color: {self.tile_color};")
                button.setEnabled(True)
                
        self.place_mines()
        
    def show_about(self):
        """Display the 'About' message box."""
        QMessageBox.information(
            self,
            "About",
            f"Minesweeper Game\nGrid: {self.grid_size}x{self.grid_size}\n"
            f"Mines: {self.num_mines}\nCreated with PySide6"
        )
        
    def show_options(self):
        """Display the options dialog for selecting map size and difficulty."""
        options_dialog = OptionsDialog(self, self.grid_size, self.num_mines)
        if options_dialog.exec() == QDialog.Accepted:
            self.grid_size = options_dialog.get_grid_size()
            self.num_mines = options_dialog.get_num_mines()
            self.setWindowTitle(f"qtMinesweeper - {self.grid_size}x{self.grid_size}")
            self.recreate_grid()
            
    def recreate_grid(self):
        """Destroy the old grid and create a new one with updated settings."""
        # Clear the old grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self.buttons = []
        self.mines = set()
        self.flags = set()
        self.create_grid()


class OptionsDialog(QDialog):
    def __init__(self, parent, current_grid_size, current_num_mines):
        super().__init__(parent)
        self.setWindowTitle("Options")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Map Size selection
        size_label = QLabel("Map Size:")
        layout.addWidget(size_label)
        
        self.size_group = QButtonGroup(self)
        normal_rb = QRadioButton("Normal (15x15)")
        large_rb = QRadioButton("Large (25x25)")
        
        if current_grid_size == 15:
            normal_rb.setChecked(True)
        else:
            large_rb.setChecked(True)
            
        self.size_group.addButton(normal_rb, 15)
        self.size_group.addButton(large_rb, 25)
        
        layout.addWidget(normal_rb)
        layout.addWidget(large_rb)
        
        # Difficulty selection
        diff_label = QLabel("Difficulty:")
        layout.addWidget(diff_label)
        
        self.diff_group = QButtonGroup(self)
        easy_rb = QRadioButton("Easy (25 mines)")
        medium_rb = QRadioButton("Medium (50 mines)")
        hard_rb = QRadioButton("Hard (75 mines)")
        
        if current_num_mines == 25:
            easy_rb.setChecked(True)
        elif current_num_mines == 50:
            medium_rb.setChecked(True)
        else:
            hard_rb.setChecked(True)
            
        self.diff_group.addButton(easy_rb, 25)
        self.diff_group.addButton(medium_rb, 50)
        self.diff_group.addButton(hard_rb, 75)
        
        layout.addWidget(easy_rb)
        layout.addWidget(medium_rb)
        layout.addWidget(hard_rb)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def get_grid_size(self):
        return self.size_group.checkedId()
        
    def get_num_mines(self):
        return self.diff_group.checkedId()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = Minesweeper()
    game.show()
    sys.exit(app.exec())
