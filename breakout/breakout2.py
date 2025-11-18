import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLACK = (0, 0, 0)
GREEN = (50, 200, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 200, 50)
ORANGE = (255, 150, 50)
PURPLE = (180, 70, 220)
PINK = (255, 100, 180)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)

BLOCK_WIDTH, BLOCK_HEIGHT = 90, 30
BALL_RADIUS = 10
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 15
BRICK_COLUMNS = 8
INITIAL_BRICK_ROWS = 5
BRICK_GAP = 5
BRICK_MARGIN_X = 30
BRICK_MARGIN_Y = 50
ROW_ADD_INTERVAL = 30000  # 30 seconds in milliseconds

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Breaker")
clock = pygame.time.Clock()

# Font
font = pygame.font.SysFont(None, 36)
title_font = pygame.font.SysFont(None, 72)
small_font = pygame.font.SysFont(None, 24)

# Particle system for effects
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 5)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = random.randint(20, 40)
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        self.size = max(0, self.size - 0.1)
        return self.life > 0
        
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

# Game variables
class Game:
    def __init__(self):
        self.reset()
        self.particles = []
        self.colors = [GREEN, BLUE, YELLOW, ORANGE, PURPLE, PINK]
        self.initialize_bricks()
        
    def reset(self):
        self.paddle_x = (WIDTH - PADDLE_WIDTH) // 2
        self.paddle_y = HEIGHT - 40
        self.ball_x, self.ball_y = WIDTH // 2, HEIGHT // 2
        self.ball_dx, self.ball_dy = 0, 0
        self.lives = 3
        self.score = 0
        self.bricks = []
        self.rows_created = 0
        self.last_row_add_time = pygame.time.get_ticks()
        self.ball_moving = False
        self.game_state = "start"  # "start", "playing", "game_over"
        
    def add_brick_row(self, initializing=False):
        """Add a new row of bricks. Existing bricks are shifted down unless initializing."""
        row_index = self.rows_created
        if not initializing:
            # Shift existing bricks down
            for brick, _ in self.bricks:
                brick.y += BLOCK_HEIGHT + BRICK_GAP
            y_position = BRICK_MARGIN_Y
        else:
            y_position = BRICK_MARGIN_Y + row_index * (BLOCK_HEIGHT + BRICK_GAP)

        row_color = self.colors[row_index % len(self.colors)]
        for i in range(BRICK_COLUMNS):
            x_position = BRICK_MARGIN_X + i * (BLOCK_WIDTH + BRICK_GAP)
            brick_rect = pygame.Rect(x_position, y_position, BLOCK_WIDTH, BLOCK_HEIGHT)
            self.bricks.append((brick_rect, row_color))

        self.rows_created += 1

    def initialize_bricks(self):
        """Populate the starting bricks."""
        self.bricks = []
        self.rows_created = 0
        for _ in range(INITIAL_BRICK_ROWS):
            self.add_brick_row(initializing=True)
            
    def add_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
            
    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]
        
    def draw_particles(self, surface):
        for particle in self.particles:
            particle.draw(surface)

# Create game instance
game = Game()

# Game loop
def game_loop():
    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if game.game_state == "start" and event.key == pygame.K_SPACE:
                    game.game_state = "playing"
                elif game.game_state == "game_over" and event.key == pygame.K_SPACE:
                    game.reset()
                    game.game_state = "playing"
                elif game.game_state == "game_over" and event.key == pygame.K_ESCAPE:
                    game.reset()
                    game.game_state = "start"
                    
                # Start ball movement on first key press
                if game.game_state == "playing" and not game.ball_moving:
                    if event.key in [pygame.K_a, pygame.K_d, pygame.K_LEFT, pygame.K_RIGHT]:
                        game.ball_dx, game.ball_dy = 5, -5
                        game.ball_moving = True

        if game.game_state == "playing":
            # Paddle movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                game.paddle_x = max(0, game.paddle_x - 8)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                game.paddle_x = min(WIDTH - PADDLE_WIDTH, game.paddle_x + 8)

            # Ball movement
            if game.ball_moving:
                game.ball_x += game.ball_dx
                game.ball_y += game.ball_dy

            # Collision with walls
            if game.ball_x <= BALL_RADIUS or game.ball_x >= WIDTH - BALL_RADIUS:
                game.ball_dx = -game.ball_dx
            if game.ball_y <= BALL_RADIUS:
                game.ball_dy = -game.ball_dy
            if game.ball_y >= HEIGHT:
                game.lives -= 1
                if game.lives <= 0:
                    game.game_state = "game_over"
                else:
                    # Reset ball
                    game.ball_x, game.ball_y = WIDTH // 2, HEIGHT // 2
                    game.ball_dx, game.ball_dy = 0, 0
                    game.ball_moving = False

            # Collision with paddle
            paddle_rect = pygame.Rect(game.paddle_x, game.paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            ball_rect = pygame.Rect(game.ball_x - BALL_RADIUS, game.ball_y - BALL_RADIUS, 
                                   BALL_RADIUS * 2, BALL_RADIUS * 2)
            
            if paddle_rect.colliderect(ball_rect) and game.ball_dy > 0:
                # Calculate bounce angle based on where ball hits paddle
                hit_pos = (game.ball_x - game.paddle_x) / PADDLE_WIDTH
                angle = (hit_pos - 0.5) * math.pi / 2  # -45° to 45°
                speed = math.sqrt(game.ball_dx**2 + game.ball_dy**2)
                game.ball_dx = math.sin(angle) * speed
                game.ball_dy = -math.cos(angle) * speed

            # Collision with bricks
            ball_rect = pygame.Rect(game.ball_x - BALL_RADIUS, game.ball_y - BALL_RADIUS, 
                                   BALL_RADIUS * 2, BALL_RADIUS * 2)
            for brick, color in game.bricks[:]:
                if brick.colliderect(ball_rect):
                    game.bricks.remove((brick, color))
                    game.ball_dy = -game.ball_dy
                    game.score += 10
                    # Add particles
                    game.add_particles(brick.centerx, brick.centery, color)
                    break

            # Add new row of bricks periodically
            current_time = pygame.time.get_ticks()
            if current_time - game.last_row_add_time >= ROW_ADD_INTERVAL:
                game.add_brick_row()
                game.last_row_add_time = current_time

            # Update particles
            game.update_particles()

            # Check win condition
            if not game.bricks:
                game.initialize_bricks()

        # Drawing
        screen.fill(DARK_GRAY)
        
        if game.game_state == "start":
            # Draw title
            title = title_font.render("BRICK BREAKER", True, WHITE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
            
            # Draw instructions
            instructions = [
                "Use A/D or Arrow Keys to move paddle",
                "Press SPACE to start",
                "Break all bricks to win!",
                "Don't let the ball fall!"
            ]
            
            for i, line in enumerate(instructions):
                text = small_font.render(line, True, LIGHT_GRAY)
                screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + i*30))
                
            pygame.display.flip()
            clock.tick(60)
            continue
            
        elif game.game_state == "game_over":
            # Draw game over screen
            screen.fill(BLACK)
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//3))
            
            score_text = font.render(f"Final Score: {game.score}", True, WHITE)
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
            
            restart_text = font.render("Press SPACE to restart or ESC for menu", True, LIGHT_GRAY)
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 100))
            
            pygame.display.flip()
            clock.tick(60)
            continue

        # Draw paddle with gradient effect
        pygame.draw.rect(screen, WHITE, (game.paddle_x, game.paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(screen, LIGHT_GRAY, (game.paddle_x, game.paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT//2))

        # Draw ball
        pygame.draw.circle(screen, RED, (int(game.ball_x), int(game.ball_y)), BALL_RADIUS)
        pygame.draw.circle(screen, (255, 200, 200), (int(game.ball_x), int(game.ball_y)), BALL_RADIUS-3)

        # Draw bricks with borders
        for brick, color in game.bricks:
            pygame.draw.rect(screen, color, brick)
            pygame.draw.rect(screen, DARK_GRAY, brick, 2)

        # Draw particles
        game.draw_particles(screen)

        # Draw score and lives
        score_text = font.render(f'Score: {game.score}', True, WHITE)
        lives_text = font.render(f'Lives: {game.lives}', True, WHITE)
        screen.blit(score_text, (20, 10))
        screen.blit(lives_text, (WIDTH - lives_text.get_width() - 20, 10))

        pygame.display.flip()
        clock.tick(60)

# Start the game
game_loop()