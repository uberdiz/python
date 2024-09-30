import pygame
import random

# Initialize pygame and game window
pygame.init()
screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Python Snake")

# Game variables
cell_size = 20
direction = 1  # 1 is up, 2 is right, 3 is down, 4 is left
update_snake = 0
new_food = True
food = [0, 0]
score = 0
game_over = False

# Snake game variables
snake_pos = [
    [int(screen_width / 2), int(screen_height / 2)],
    [int(screen_width / 2), int(screen_height / 2) + cell_size],
    [int(screen_width / 2), int(screen_height / 2) + cell_size * 2]
]

#define font
font = pygame.font.SysFont('Arial', 40)


# Colors
bg = (255, 200, 150)
snake_inner = (50, 175, 25)
snake_outer = (100, 100, 200)
red = (255, 0, 0)
orange = (255, 150, 0)
black = (0, 0, 0)

# Set up rectangle for play agian
again_rect = pygame.Rect(screen_width // 2 - 100, screen_height // 2 - 50, 200, 100)


# Function to draw the game screen
def draw_screen():
    screen.fill(bg)

def draw_score():
    score_text = "Score: " + str(score)
    score_image = font.render(score_text, True, black)
    screen.blit(score_image, (0, 0))

def check_game_over(game_over):
    #Check is snake ate itself
    head_count = 0
    for x in snake_pos:
        if snake_pos[0] == x and head_count > 0:
            game_over = True
        head_count += 1
    #Out of Bounds
    if snake_pos[0][0] < 0 or snake_pos[0][0] > screen_width or snake_pos[0][1] < 0 or snake_pos[0][1] > screen_height:
        game_over = True
    return game_over

def draw_game_over():
    game_over_text = "Game Over"
    game_over_image = font.render(game_over_text, True, black)
    screen.blit(game_over_image, (screen_width // 2 - 100, screen_height // 2 - 50))

    again_text = "Press 'Enter' to play again"
    again_text_image = font.render(again_text, True, black)
    screen.blit(again_text_image, (screen_width // 2 - 100, screen_height // 2 + 50))
# Game loop
run = True
while run:
    # Refresh screen
    draw_screen()
    draw_score()
    # Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w and direction != 3:  # Prevent moving in the opposite direction
                direction = 1  # Move up
            if event.key == pygame.K_d and direction != 4:
                direction = 2  # Move right
            if event.key == pygame.K_s and direction != 1:
                direction = 3  # Move down
            if event.key == pygame.K_a and direction != 2:
                direction = 4  # Move left

    # Create food
    if new_food:
        new_food = False
        food = [random.randrange(0, screen_width, cell_size), random.randrange(0, screen_height, cell_size)]

    # Draw food
    pygame.draw.rect(screen, red, pygame.Rect(food[0], food[1], cell_size, cell_size))

    if not game_over:
        # Move snake
        if update_snake > 99:
            update_snake = 0

            # Get new head position based on direction
            head_x, head_y = snake_pos[0]
            if direction == 1:  # Up
                head_y -= cell_size
            elif direction == 2:  # Right
                head_x += cell_size
            elif direction == 3:  # Down
                head_y += cell_size
            elif direction == 4:  # Left
                head_x -= cell_size

            # Insert new head position
            new_head = [head_x, head_y]
            snake_pos = [new_head] + snake_pos[:-1]

            game_over = check_game_over(game_over)

    if game_over:
        draw_game_over()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Reset game variables
                snake_pos = [
                    [int(screen_width / 2), int(screen_height / 2)],
                    [int(screen_width / 2), int(screen_height / 2) + cell_size],
                    [int(screen_width / 2), int(screen_height / 2) + cell_size * 2]
                ]
                direction = 1
                update_snake = 0
                new_food = True
                food = [0, 0]
                score = 0
                game_over = False


    # Check if food is eaten
    if snake_pos[0] == food:
        new_food = True
        # Add new segment at the tail
        snake_pos.append(snake_pos[-1])

        # Increase score
        score += 1

    # Draw snake
    head = 1
    for segment in snake_pos:
        if head == 0:
            pygame.draw.rect(screen, snake_outer, pygame.Rect(segment[0], segment[1], cell_size, cell_size))
            pygame.draw.rect(screen, snake_inner, pygame.Rect(segment[0] + 1, segment[1] + 1, cell_size - 2, cell_size - 2))
        if head == 1:
            pygame.draw.rect(screen, snake_outer, pygame.Rect(segment[0], segment[1], cell_size, cell_size))
            pygame.draw.rect(screen, orange, pygame.Rect(segment[0] + 1, segment[1] + 1, cell_size - 2, cell_size - 2))
            head = 0

    # Refresh screen
    pygame.display.update()
    update_snake += 1

pygame.quit()
