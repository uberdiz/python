import pygame
# Game Window
pygame.init()
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# 4 arguments, first 2 for x and y coordinates and the next 2 are width and height 
player = pygame.Rect((640, 360, 50, 50))

# Game loop
run = True
while run:
    # Refresh screen
    screen.fill((0, 0, 0))


    # 3 arguments, screen, color to draw, and thing to draw
    pygame.draw.rect(screen , (255, 0, 255), player)

    # Key capture
    key = pygame.key.get_pressed()
    # Movement
    if key[pygame.K_a] == True: #Looking for 'a' key to be pressed
        # Move in place. x and y coordinates
        player.move_ip(-1, 0)
    elif key[pygame.K_d] == True:
        player.move_ip(1,0)
    elif key[pygame.K_w] == True:
        player.move_ip(0,-1)
    elif key[pygame.K_s] == True:
        player.move_ip(0,1)
    # Event handler
    for event in pygame.event.get():
       
        
        # X button in the top
        if event.type == pygame.QUIT:
            run = False
    #refresh screen
    pygame.display.update()

pygame.quit()
