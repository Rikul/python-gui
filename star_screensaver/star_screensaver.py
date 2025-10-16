import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Get display information
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h

# Screen dimensions
WIDTH, HEIGHT = screen_width, screen_height
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Starfield Simulation")

# Star properties
NUM_STARS = 250 # Number of stars
MAX_SPEED = 4 # Maximum speed of stars

class Star:
    def __init__(self):
        """ Initialize star with random position and speed """
        self.x = random.uniform(-WIDTH // 2, WIDTH // 2)
        self.y = random.uniform(-HEIGHT // 2, HEIGHT // 2)
        self.z = random.uniform(1, WIDTH)  # Depth for perspective effect
        self.speed = random.uniform(1, MAX_SPEED)


    def update(self):
        """ Move star forward and reset if it goes out of view """
        self.z -= self.speed  # Move the star forward
        if self.z <= 0:
            self.reset()

    def reset(self):
        """ Reset star to a new random position far away """
        self.x = random.uniform(-WIDTH // 2, WIDTH // 2)
        self.y = random.uniform(-HEIGHT // 2, HEIGHT // 2)
        self.z = WIDTH  # Reset depth
        self.speed = random.uniform(1, MAX_SPEED)

    def draw(self, screen):
        """ Draw star with perspective scaling """
        sx = int((self.x / self.z) * WIDTH + WIDTH // 2)
        sy = int((self.y / self.z) * HEIGHT + HEIGHT // 2)
        size = int((1 - self.z / WIDTH) * 5)  # Stars appear bigger when closer
        size = max(size, 1)

        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
            pygame.draw.circle(screen, (255, 255, 255), (sx, sy), size)

def display_menu(screen):
    """ Display a menu with options to change settings or exit """
    menu_items = {"Options" : 0, "Exit" : 1}
    font = pygame.font.SysFont(None, 48)
    WHITE = (255,255,255)
    GRAY = (150, 150, 150)
    options_color = WHITE
    exit_color = GRAY
    selected_item = 0


    menu_open = True
    while menu_open:
        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_open = False
                elif event.key == pygame.K_RETURN:
                    if selected_item == menu_items["Options"]:
                        # Placeholder for options menu
                        # Do nothing for now
                        pass
                    elif selected_item == menu_items["Exit"]:
                        pygame.quit()
                        sys.exit()
                elif event.key == pygame.K_DOWN:
                    if selected_item == menu_items["Options"]:
                        selected_item = menu_items["Exit"]
                        options_color = GRAY
                        exit_color = WHITE
                elif event.key == pygame.K_UP:
                    if selected_item == menu_items["Exit"]:
                        selected_item = menu_items["Options"]
                        options_color = WHITE
                        exit_color = GRAY

        screen.fill((0, 0, 0))
        options_text = font.render('Options', True, options_color)
        exit_text = font.render('Exit', True, exit_color)
        screen.blit(options_text, (WIDTH // 2 - options_text.get_width() // 2, HEIGHT // 2 - 60))
        screen.blit(exit_text, (WIDTH // 2 - exit_text.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()


    pygame.display.flip()
                    

def main():
    clock = pygame.time.Clock()
    stars = [Star() for _ in range(NUM_STARS)]
    running = True
    paused = False

    # Main loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_ESCAPE:
                    display_menu(screen)

        if not paused:
            screen.fill((0, 0, 0))

            for star in stars:
                star.update()
                star.draw(screen)

            pygame.display.flip()

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()