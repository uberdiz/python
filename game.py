import pygame as pg
import random

# Initialize Pygame
pg.init()
screen = pg.display.set_mode((800, 600))
pg.display.set_caption("My First Pygame Window")

# Define colors
screen_color = (80, 80, 255)
rectangle_color = (0, 255, 0)

# Rectangle position and size
ground = pg.Rect(350, 250, 50, 50)
speed = 1

running = True
while running:
    screen_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    screen.fill(screen_color)

    # Handle continuous key presses
    keys = pg.key.get_pressed()
    if keys[pg.K_w] and ground.y > 0:
        ground.y -= speed
    if keys[pg.K_s] and ground.y < 600 - ground.height:
        ground.y += speed
    if keys[pg.K_a] and ground.x > 0:
        ground.x -= speed
    if keys[pg.K_d] and ground.x < 800 - ground.width:
        ground.x += speed

    # Draw the rectangle
    pg.draw.rect(screen, rectangle_color, ground)

    # Handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Update the display
    pg.display.flip()

pg.quit()
