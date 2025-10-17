import tkinter as tk
from tkinter import messagebox, font
import random

class Minesweeper:
    def __init__(self, Master, grid_size=15, num_mines=25):
        self.Master = Master
        self.grid_size = grid_size
        self.num_mines = num_mines
        self.tile_color = "lightgrey"

        self.Master.title(f"tkMinesweeper - {self.grid_size}x{self.grid_size}")
        # Remove fixed geometry to allow automatic sizing
        self.Master.resizable(False, False)
        self.Master.withdraw() # hide the window initially

        # Create the menu bar
        self.MenuBar = tk.Menu(self.Master)
        self.Master.config(menu=self.MenuBar)

        # Add "Game" menu
        GameMenu = tk.Menu(self.MenuBar, tearoff=0)
        GameMenu.add_command(label="New Game", command=self.NewGame)
        GameMenu.add_command(label="Options", command=self.ShowOptions)
        GameMenu.add_separator()
        GameMenu.add_command(label="Exit", command=self.Master.quit)
        self.MenuBar.add_cascade(label="Game", menu=GameMenu)

        # Add "Help" menu
        HelpMenu = tk.Menu(self.MenuBar, tearoff=0)
        HelpMenu.add_command(label="About", command=self.ShowAbout)
        self.MenuBar.add_cascade(label="Help", menu=HelpMenu)

        # Emoji icons for mines and flags
        self.MineIcon = "💥"    # "💣"
        self.FlagIcon = "🚩"

        # Create the grid
        self.GridFrame = tk.Frame(self.Master)
        self.GridFrame.pack()
        
        self.Buttons = []
        self.Mines = set()
        self.Flags = set()
        self.CreateGrid()

    def CreateGrid(self):
        """
        Create a grid of buttons for the game board.
        """

        button_width = 5
        button_height = 2
        if self.grid_size != 15:
            button_width = 3
            button_height = 1

        for Row in range(self.grid_size):
            ButtonRow = []
            for Col in range(self.grid_size):
                ButtonFont = font.Font(family="system", weight=font.BOLD, size=16)
                Button = tk.Button(
                    self.GridFrame, font=ButtonFont, bg=self.tile_color, width=button_width, height=button_height
                )
                Button.bind('<Button-1>', lambda event, r=Row, c=Col: self.OnLeftClick(r, c))
                Button.bind('<Button-3>', lambda event, r=Row, c=Col: self.OnRightClick(r, c))
                Button.grid(row=Row, column=Col)
                ButtonRow.append(Button)

            self.Buttons.append(ButtonRow)
        self.PlaceMines()
        
        # Size window to fit the grid
        self.Master.update_idletasks()  # Let tkinter calculate sizes
        width = self.GridFrame.winfo_reqwidth()
        height = self.GridFrame.winfo_reqheight()

        screen_width = self.Master.winfo_screenwidth()
        screen_height = self.Master.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.Master.geometry(f"{width}x{height}+{x}+{y}")
        self.Master.deiconify()  # Show the window after sizing and centering

    def PlaceMines(self):
        """
        Create a set of random mine positions on the grid.
        """
        self.Mines = set(random.sample(range(self.grid_size * self.grid_size), self.num_mines))  # Choose random positions for mines

    def CountAdjacentMines(self, Row, Col):
        """
        Count the number of mines around a given position.

        Parameters:
        Row (int): The row index of the position.
        Col (int): The column index of the position.

        Returns:
        int: The number of mines adjacent to the position.
        """
        Count = 0
        for r in range(Row-1, Row+2):
            for c in range(Col-1, Col+2):
                if 0 <= r < self.grid_size and 0 <= c < self.grid_size:  # Stay within bounds
                    if (r * self.grid_size + c) in self.Mines:
                        Count += 1
        return Count

    def RevealTile(self, Row, Col):
        """
        Reveal the tile and its adjacent tiles if it has 0 adjacent mines.

        Parameters:
        Row (int): The row index of the tile.
        Col (int): The column index of the tile.
        """
        if Row < 0 or Row >= self.grid_size or Col < 0 or Col >= self.grid_size:
            return  # Out of bounds
        Button = self.Buttons[Row][Col]
        if (Row, Col) in self.Flags:
            return
        if Button['state'] == tk.DISABLED:
            return  # Already revealed or marked

        Count = self.CountAdjacentMines(Row, Col)
        Button.config(state=tk.DISABLED, bg='white')
        if Count > 0:
            Button.config(text=str(Count))
        else:
            # Recursively reveal adjacent tiles if the count is 0
            for r in range(Row-1, Row+2):
                for c in range(Col-1, Col+2):
                    self.RevealTile(r, c)

    def OnLeftClick(self, Row, Col):
        """
        Handle the left-click event.

        Parameters:
        Row (int): The row index of the clicked button.
        Col (int): The column index of the clicked button.
        """
        Index = Row * self.grid_size + Col
        if (Row, Col) in self.Flags:
            return
        if Index in self.Mines:
            self.ShowMine()
            messagebox.showinfo("Game Over", "You clicked on a mine!")
            self.Master.after(100, self.NewGame)  # Delay the new game start slightly
        else:
            self.RevealTile(Row, Col)

    def OnRightClick(self, Row, Col):
        """
        Handle the right-click event to mark a button.

        Parameters:
        Row (int): The row index of the button.
        Col (int): The column index of the button.
        """
        Button = self.Buttons[Row][Col]
        if Button['state'] != tk.NORMAL and Button['text'] != self.FlagIcon:
            return

        if (Row, Col) in self.Flags:
            self.Flags.remove((Row, Col))
            if Button['state'] == tk.DISABLED:
                return
            Button.config(text='', bg=self.tile_color)
        else:
            if Button['state'] == tk.DISABLED:
                return
            self.Flags.add((Row, Col))
            Button.config(text=self.FlagIcon, bg='lightyellow')

    def ShowMine(self):
        """
        Reveal all tiles on the board and disable all buttons.
        """
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                btn = self.Buttons[row][col]
                index = row * self.grid_size + col
                if index in self.Mines:
                    btn.config(text=self.MineIcon, bg='lightyellow', state=tk.DISABLED)
                else:
                    count = self.CountAdjacentMines(row, col)
                    btn.config(text=str(count) if count > 0 else '', bg='white', state=tk.DISABLED)

    def NewGame(self):
        """
        Start a new game by resetting the board and placing new mines.
        """
        self.Mines.clear()
        self.Flags.clear()
        for Row in self.Buttons:
            for Button in Row:
                Button.config(text='', bg=self.tile_color, state=tk.NORMAL)
        self.PlaceMines()

    def ShowAbout(self):
        """
        Display the 'About' message box.
        """
        messagebox.showinfo("About", f"Minesweeper Game\nGrid: {self.grid_size}x{self.grid_size}\nMines: {self.num_mines}\nCreated with Tkinter")

    def ShowOptions(self):
        """
        Display the options dialog for selecting map size and difficulty.
        """
        options_window = tk.Toplevel(self.Master)
        options_window.title("Options")
        options_window.resizable(False, False)

        # Map Size selection
        size_label = tk.Label(options_window, text="Map Size:")
        size_label.pack(pady=5)

        self.size_var = tk.StringVar(value="Normal" if self.grid_size == 15 else "Large")
        normal_rb = tk.Radiobutton(options_window, text="Normal (15x15)", variable=self.size_var, value="Normal")
        normal_rb.pack()
        large_rb = tk.Radiobutton(options_window, text="Large (25x25)", variable=self.size_var, value="Large")
        large_rb.pack()

        # Difficulty selection
        diff_label = tk.Label(options_window, text="Difficulty:")
        diff_label.pack(pady=5)

        current_diff = "Easy" if self.num_mines == 25 else ("Medium" if self.num_mines == 50 else "Hard")
        self.diff_var = tk.StringVar(value=current_diff)
        easy_rb = tk.Radiobutton(options_window, text="Easy (25 mines)", variable=self.diff_var, value="Easy")
        easy_rb.pack()
        medium_rb = tk.Radiobutton(options_window, text="Medium (50 mines)", variable=self.diff_var, value="Medium")
        medium_rb.pack()
        hard_rb = tk.Radiobutton(options_window, text="Hard (75 mines)", variable=self.diff_var, value="Hard")
        hard_rb.pack()

        # Buttons
        button_frame = tk.Frame(options_window)
        button_frame.pack(pady=10)
        ok_button = tk.Button(button_frame, text="OK", command=lambda: self.ApplyOptions(options_window))
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = tk.Button(button_frame, text="Cancel", command=options_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        # Center the options window
        options_window.update_idletasks()
        width = options_window.winfo_reqwidth()
        height = options_window.winfo_reqheight()
        screen_width = options_window.winfo_screenwidth()
        screen_height = options_window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        options_window.geometry(f"{width}x{height}+{x}+{y}")

    def ApplyOptions(self, window):
        """
        Apply the selected options and recreate the grid.
        """
        size = self.size_var.get()
        diff = self.diff_var.get()
        if size == "Normal":
            self.grid_size = 15
        else:
            self.grid_size = 25
        if diff == "Easy":
            self.num_mines = 25
        elif diff == "Medium":
            self.num_mines = 50
        else:
            self.num_mines = 75
        self.Master.title(f"tkMinesweeper - {self.grid_size}x{self.grid_size}")
        window.destroy()
        self.RecreateGrid()

    def RecreateGrid(self):
        """
        Destroy the old grid and create a new one with updated settings.
        """
        self.GridFrame.destroy()
        self.GridFrame = tk.Frame(self.Master)
        self.GridFrame.pack()
        self.Buttons = []
        self.Mines = set()
        self.Flags = set()
        self.CreateGrid()

if __name__ == "__main__":
    Root = tk.Tk()
    Game = Minesweeper(Root)
    Root.mainloop()
