import pygame
# Game Window
pygame.init()
screen_width = 1280
screen_height = 720

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Python Snake")
# 4 arguments, first 2 for x and y coordinates and the next 2 are width and height 

# Game variables
cell_size = 10
direction = 1 # 1 is up 2 is right 3 is down 4 is left

#Snake game variables
snake_pos = [[int(screen_width / 2), int(screen_height / 2)]]
snake_pos.append([int(screen_width / 2), int(screen_height / 2) + cell_size])
snake_pos.append([int(screen_width / 2), int(screen_height / 2) + cell_size *2])
snake_pos.append([int(screen_width / 2), int(screen_height / 2) + cell_size *3])
snake_pos.append([int(screen_width / 2), int(screen_height / 2) + cell_size *4]) 


# Colors
bg = (255,200,150)
snake_inner = (50, 175, 25)
snake_outer = (100, 100, 200)
red = (255, 0, 0)


# Game loop function
def draw_screen():
    screen.fill(bg)
# Game loop
run = True
while run:
    # Refresh screen
    draw_screen()

    
    # Event handler
    for event in pygame.event.get():
       # X button in the top
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_W:
                direction = 1
            elif event.key == pygame.K_D:
                direction = 2
            elif event.key == pygame.K_S:
                direction = 3
            elif event.key == pygame.K_A:
                direction = 4
    
	#Draw snake
    head = 1
    for x in snake_pos:
        if head == 0:
        	#                screen, color,       rectangle  (x,    y,    width,     height)
            pygame.draw.rect(screen, snake_outer, pygame.Rect(x[0], x[1], cell_size, cell_size))
            pygame.draw.rect(screen, snake_inner, pygame.Rect(x[0] + 1, x[1] + 1, cell_size - 2, cell_size - 2))
        if head == 1:
            pygame.draw.rect(screen, snake_outer, pygame.Rect(x[0], x[1], cell_size, cell_size))
            pygame.draw.rect(screen, red, pygame.Rect(x[0] + 1, x[1] + 1, cell_size - 2, cell_size - 2))
            head = 0
            
	
	#refresh screen
    pygame.display.update()

pygame.quit()