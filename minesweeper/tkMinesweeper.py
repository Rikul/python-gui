import tkinter as tk
from tkinter import messagebox, font
import random

class Minesweeper:
    def __init__(self, Master):
        self.Master = Master
        self.Master.title("Minesweeper")
        self.Master.geometry("500x500")
        self.Master.resizable(False, False)
        
        # Create the menu bar
        self.MenuBar = tk.Menu(self.Master)
        self.Master.config(menu=self.MenuBar)

        # Add "Game" menu
        GameMenu = tk.Menu(self.MenuBar, tearoff=0)
        GameMenu.add_command(label="New Game", command=self.NewGame)
        GameMenu.add_separator()
        GameMenu.add_command(label="Exit", command=self.Master.quit)
        self.MenuBar.add_cascade(label="Game", menu=GameMenu)

        # Add "Help" menu
        HelpMenu = tk.Menu(self.MenuBar, tearoff=0)
        HelpMenu.add_command(label="About", command=self.ShowAbout)
        self.MenuBar.add_cascade(label="Help", menu=HelpMenu)

        # Emoji icons for mines and flags
        self.MineIcon = "💣"
        self.FlagIcon = "🚩"

        # Create the grid
        self.GridFrame = tk.Frame(self.Master)
        self.GridFrame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.Buttons = []
        self.Mines = set()
        self.CreateGrid()

    def CreateGrid(self):
        """
        Create a 10x10 grid of buttons for the game board.
        """
        for Row in range(10):
            ButtonRow = []
            for Col in range(10):
                ButtonFont = font.Font(weight="bold", size=10)
                Button = tk.Button(
                    self.GridFrame, font=ButtonFont, bg='lightblue', width=4, height=2
                )
                Button.bind('<Button-1>', lambda event, r=Row, c=Col: self.OnLeftClick(r, c))
                Button.bind('<Button-3>', lambda event, r=Row, c=Col: self.OnRightClick(r, c))
                Button.grid(row=Row, column=Col)
                ButtonRow.append(Button)
            self.Buttons.append(ButtonRow)
        self.PlaceMines()

    def PlaceMines(self):
        """
        Create a set of 10 random mine positions on the grid.
        """
        self.Mines = set(random.sample(range(100), 10))  # Choose 10 random positions for mines

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
                if 0 <= r < 10 and 0 <= c < 10:  # Stay within bounds
                    if (r * 10 + c) in self.Mines:
                        Count += 1
        return Count

    def RevealTile(self, Row, Col):
        """
        Reveal the tile and its adjacent tiles if it has 0 adjacent mines.

        Parameters:
        Row (int): The row index of the tile.
        Col (int): The column index of the tile.
        """
        if Row < 0 or Row >= 10 or Col < 0 or Col >= 10:
            return  # Out of bounds
        Button = self.Buttons[Row][Col]
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
        Index = Row * 10 + Col
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
        if Button['state'] == tk.NORMAL:
            Button.config(text=self.FlagIcon, bg='lightyellow', state=tk.DISABLED)
        elif Button['state'] == tk.DISABLED and Button['text'] == self.FlagIcon:
            Button.config(text='', bg='lightblue', state=tk.NORMAL)

    def ShowMine(self):
        """
        Display all mines on the board.
        """
        for Index in self.Mines:
            Row, Col = divmod(Index, 10)
            self.Buttons[Row][Col].config(text=self.MineIcon, bg='red', state=tk.DISABLED)

    def NewGame(self):
        """
        Start a new game by resetting the board and placing new mines.
        """
        self.Mines.clear()
        for Row in self.Buttons:
            for Button in Row:
                Button.config(text='', bg='lightblue', state=tk.NORMAL)
        self.PlaceMines()

    def ShowAbout(self):
        """
        Display the 'About' message box.
        """
        messagebox.showinfo("About", "Minesweeper Game\nCreated with Tkinter")

if __name__ == "__main__":
    Root = tk.Tk()
    Game = Minesweeper(Root)
    Root.mainloop()