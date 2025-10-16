import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 500               # Width of the game window
SCREEN_HEIGHT = 500              # Height of the game window
BACKGROUND_COLOR = (255, 255, 255)  # White background
LINE_COLOR = (0, 0, 0)           # Black lines for the grid
O_COLOR = (0, 255, 0)            # Green for O
X_COLOR = (0, 0, 0)              # Black for X
FONT_COLOR = (255, 255, 255)     # White for font display
LINE_WIDTH = 15                   # Thickness of grid lines
CELL_SIZE = SCREEN_WIDTH // 3     # Size of each cell in the grid

class TicTacToe:
    def __init__(self):
        # Initialize game state variables
        self.board = [["" for _ in range(3)] for _ in range(3)]  # 3x3 game board
        self.current_player = "X"  # Start with player X
        self.game_over = False      # Flag to check if the game is over
        self.winner = None          # Variable to store the winner

        # Set up the Pygame screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tic-Tac-Toe")  # Window title

    def run_game(self):
        """Main game loop to handle events and draw the board."""
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  # Exit the game

                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    # Get mouse position for player move
                    mouse_x, mouse_y = event.pos
                    row = mouse_y // CELL_SIZE
                    col = mouse_x // CELL_SIZE

                    # Check if the cell is empty
                    if self.board[row][col] == "":
                        self.board[row][col] = self.current_player  # Place the player's symbol
                        if self.check_winner():  # Check for a winner
                            self.game_over = True
                        else:
                            if self.check_tie():  # Check for a tie
                                self.game_over = True
                                self.winner = None  # No winner in case of a tie
                            else:
                                # Switch players
                                self.current_player = "O" if self.current_player == "X" else "X"

            self.draw_board()  # Draw the game board

            if self.game_over:  # If the game is over, display the result
                self.display_result()

            pygame.display.flip()  # Update the display
            if self.game_over:  # Delay for a while if the game is over
                time.sleep(4)
                self.reset_game()  # Reset the game for a new round

    def draw_board(self):
        """Draw the game board and the symbols."""
        # Clear the screen
        self.screen.fill(BACKGROUND_COLOR)

        # Draw grid lines
        for i in range(1, 3):
            pygame.draw.line(self.screen, LINE_COLOR, (0, CELL_SIZE * i), (SCREEN_WIDTH, CELL_SIZE * i), LINE_WIDTH)
            pygame.draw.line(self.screen, LINE_COLOR, (CELL_SIZE * i, 0), (CELL_SIZE * i, SCREEN_HEIGHT), LINE_WIDTH)

        # Draw X's and O's on the board
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == "X":
                    # Draw X
                    pygame.draw.line(self.screen, X_COLOR, (col * CELL_SIZE + 20, row * CELL_SIZE + 20),
                                     (col * CELL_SIZE + CELL_SIZE - 20, row * CELL_SIZE + CELL_SIZE - 20), LINE_WIDTH)
                    pygame.draw.line(self.screen, X_COLOR, (col * CELL_SIZE + CELL_SIZE - 20, row * CELL_SIZE + 20),
                                     (col * CELL_SIZE + 20, row * CELL_SIZE + CELL_SIZE - 20), LINE_WIDTH)
                elif self.board[row][col] == "O":
                    # Draw O
                    pygame.draw.circle(self.screen, O_COLOR, (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 20, LINE_WIDTH)

    def check_tie(self):
        """Check if the game is a tie (no empty cells left)."""
        for row in self.board:
            if "" in row:  # If there's any empty cell, it's not a tie
                return False
        return True  # All cells are filled, it's a tie

    def check_winner(self):
        """Check for a winner in rows, columns, and diagonals."""
        # Check rows and columns for a winner
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != "":
                self.winner = self.board[i][0]  # Winner found in a row
                return True
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != "":
                self.winner = self.board[0][i]  # Winner found in a column
                return True

        # Check diagonals for a winner
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "":
            self.winner = self.board[0][0]  # Winner found in the main diagonal
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "":
            self.winner = self.board[0][2]  # Winner found in the anti-diagonal
            return True

        return False  # No winner found

    def display_result(self):
        """Display the result of the game (winner or tie)."""
        self.screen.fill((0, 0, 0))  # Fill the screen with black

        # Display the winner or tie message
        font = pygame.font.Font(None, 100)
        if self.winner:
            text = font.render(f"{self.winner} wins!", True, FONT_COLOR)
            self.screen.blit(text, (100, 100))
        else:
            text = font.render("It's a tie!", True, FONT_COLOR)
            self.screen.blit(text, (100, 100))

    def reset_game(self):
        """Reset the game state for a new game."""
        self.board = [["" for _ in range(3)] for _ in range(3)]  # Reset the board
        self.current_player = "X"  # Reset current player to X
        self.game_over = False      # Reset game over flag
        self.winner = None          # Reset winner

# Entry point to start the game
if __name__ == "__main__":
    game = TicTacToe()  # Create a TicTacToe object
    game.run_game()     # Start the game