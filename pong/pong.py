import pygame
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BALL_RADIUS = 15
BALL_SPEED_X = 5
BALL_SPEED_Y = 5
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_SPEED = 5

# Initialize pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Single Player Pong")

# Colors
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Fonts
font = pygame.font.SysFont("arial", 36)
game_over_font = pygame.font.SysFont("arial", 72, bold=True)

# Ball class
class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
        self.radius = BALL_RADIUS
        self.speed_x = BALL_SPEED_X * random.choice((1, -1))
        self.speed_y = BALL_SPEED_Y * random.choice((1, -1))

    def update(self):
        self.pos[0] += self.speed_x
        self.pos[1] += self.speed_y

        # Bounce off the top and bottom
        if self.pos[1] - self.radius <= 0 or self.pos[1] + self.radius >= SCREEN_HEIGHT:
            self.speed_y *= -1

        # Bounce off the right
        if self.pos[0] + self.radius >= SCREEN_WIDTH:
            self.speed_x *= -1

    def draw(self):
        pygame.draw.circle(screen, BLUE, (int(self.pos[0]), int(self.pos[1])), self.radius)

def check_collision(ball, player_paddle):
    paddle_rect = player_paddle.rect

    # Calculate the closest point on the paddle to the ball's center
    closest_x = max(paddle_rect.left, min(ball.pos[0], paddle_rect.right))
    closest_y = max(paddle_rect.top, min(ball.pos[1], paddle_rect.bottom))

    # Calculate the distance between the closest point and the ball's center
    distance_x = ball.pos[0] - closest_x
    distance_y = ball.pos[1] - closest_y
    distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

    # If the distance is less than the ball's radius, a collision occurred
    if distance <= ball.radius:
        ball.speed_x *= -1
        ball.pos[0] += ball.speed_x * 2
        ball.pos[1] += ball.speed_y * 2
        return True
    return False

# Player paddle class
class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = PADDLE_SPEED

    def move(self, up, down):
        if up and self.rect.top > 0:
            self.rect.y -= self.speed
        if down and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

# Main game loop
def main():
    clock = pygame.time.Clock()
    ball = Ball()
    player_paddle = Paddle()
    score = 0
    high_score = 0
    game_over = False
    paused = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                if game_over and event.key == pygame.K_SPACE:
                    game_over = False
                    ball.reset()
                    player_paddle = Paddle()
                    score = 0
                
                if event.key == pygame.K_p:
                    paused = not paused
        
        if not game_over and not paused:
            keys = pygame.key.get_pressed()
            up = keys[pygame.K_UP] or keys[pygame.K_w]
            down = keys[pygame.K_DOWN] or keys[pygame.K_s]

            player_paddle.move(up, down)
            ball.update()
            
            if ball.pos[0] - ball.radius <= 0:  # Missed ball
                game_over = True
                high_score = max(high_score, score)

            if check_collision(ball, player_paddle):
                score += 100

        screen.fill((0, 0, 0))

        if game_over:
            game_over_text = game_over_font.render("GAME OVER", True, YELLOW)
            high_score_text = font.render(f"High Score: {high_score}", True, WHITE)
            restart_text = font.render("Press spacebar to restart the game", True, WHITE)

            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
            screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, SCREEN_HEIGHT // 2))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        elif paused:
            paused_text = game_over_font.render("PAUSED", True, YELLOW)
            screen.blit(paused_text, (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, SCREEN_HEIGHT // 2))
        else:
            ball.draw()
            player_paddle.draw()
            
            score_text = font.render(f"Score: {score}", True, WHITE)
            pause_text = font.render("Press P to pause", True, WHITE)
            
            screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 10, SCREEN_HEIGHT - score_text.get_height() - 10))
            screen.blit(pause_text, (10, SCREEN_HEIGHT - pause_text.get_height() - 10))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()