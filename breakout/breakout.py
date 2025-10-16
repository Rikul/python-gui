import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BLOCK_WIDTH, BLOCK_HEIGHT = 100, 30
BALL_RADIUS = 10
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 10

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Breaker")

# Game variables
paddle_x = (WIDTH - PADDLE_WIDTH) // 2
paddle_y = HEIGHT - 40
ball_x, ball_y = WIDTH // 2, HEIGHT // 2
ball_dx, ball_dy = 0, 0  # Ball starts stationary
lives = 3
score = 0
bricks = []

# Create bricks with color pattern
colors = [GREEN, BLUE, YELLOW]
for j in range(5):  # Number of rows
    for i in range(7):  # Number of columns
        brick_color = colors[j % len(colors)]
        bricks.append((pygame.Rect(i * (BLOCK_WIDTH + 10) + 25, j * (BLOCK_HEIGHT + 10) + 25, BLOCK_WIDTH, BLOCK_HEIGHT), brick_color))

# Font
font = pygame.font.Font(None, 36)

# Game loop
def game_loop():
    global paddle_x, ball_x, ball_y, ball_dx, ball_dy, score, lives, bricks

    # Flag to control ball movement
    ball_moving = False

    while True:
        screen.fill(BLACK)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Paddle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and paddle_x > 0:
            paddle_x -= 15
            ball_moving = True  # Start ball movement on paddle move
        if keys[pygame.K_d] and paddle_x < WIDTH - PADDLE_WIDTH:
            paddle_x += 15
            ball_moving = True  # Start ball movement on paddle move
        if keys[pygame.K_LEFT] and paddle_x > 0:
            paddle_x -= 15
            ball_moving = True  # Start ball movement on paddle move
        if keys[pygame.K_RIGHT] and paddle_x < WIDTH - PADDLE_WIDTH:
            paddle_x += 15
            ball_moving = True  # Start ball movement on paddle move
        
        # Ball movement
        if ball_moving:
            if ball_dx == 0 and ball_dy == 0:  # Start the ball movement
                ball_dx, ball_dy = 5, -5  # Initial ball speed
            ball_x += ball_dx
            ball_y += ball_dy

        # Collision with walls
        if ball_x <= 0 or ball_x >= WIDTH - BALL_RADIUS * 2:
            ball_dx = -ball_dx
        if ball_y <= 0:
            ball_dy = -ball_dy
        if ball_y >= HEIGHT:
            lives -= 1
            if lives == 0:
                game_over("GAME OVER")
                continue

            ball_x, ball_y = WIDTH // 2, HEIGHT // 2
            ball_dx, ball_dy = 0, 0  # Reset ball movement
            ball_moving = False  # Stop ball until player moves paddle

        # Collision with paddle
        if (paddle_y <= ball_y + BALL_RADIUS * 2 <= paddle_y + PADDLE_HEIGHT and
                paddle_x <= ball_x + BALL_RADIUS <= paddle_x + PADDLE_WIDTH):
            ball_dy = -ball_dy

        # Collision with bricks
        for brick, color in bricks[:]:
            if brick.colliderect(pygame.Rect(ball_x, ball_y, BALL_RADIUS * 2, BALL_RADIUS * 2)):
                bricks.remove((brick, color))
                ball_dy = -ball_dy
                score += 10

        # Draw paddle
        pygame.draw.rect(screen, WHITE, (paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))

        # Draw ball
        pygame.draw.circle(screen, RED, (ball_x + BALL_RADIUS, ball_y + BALL_RADIUS), BALL_RADIUS)

        # Draw bricks
        for brick, color in bricks:
            pygame.draw.rect(screen, color, brick)

        # Draw score and lives
        score_text = font.render(f'Score: {score}', True, WHITE)
        lives_text = font.render(f'Lives: {lives}', True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (WIDTH - 150, 10))

        # Check win condition
        if not bricks:
            game_over("YOU WIN")
            continue

        pygame.display.flip()
        pygame.time.delay(30)

def game_over(message):
    global lives, score, bricks
    screen.fill(BLACK)
    game_over_text = font.render(message, True, WHITE)
    text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    pygame.draw.rect(screen, BLACK, text_rect.inflate(20, 20))  # Draw box behind text
    screen.blit(game_over_text, text_rect)
    pygame.display.flip()
    pygame.time.delay(3000)
    
    # Reset game state
    lives = 3
    score = 0
    bricks = []
    for j in range(5):  # Number of rows
        for i in range(7):  # Number of columns
            brick_color = colors[j % len(colors)]
            bricks.append((pygame.Rect(i * (BLOCK_WIDTH + 10) + 25, j * (BLOCK_HEIGHT + 10) + 25, BLOCK_WIDTH, BLOCK_HEIGHT), brick_color))

# Start the game
game_loop()