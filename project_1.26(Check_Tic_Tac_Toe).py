board = [[0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]]
winX = False
winO = False
gaming = True


def print_board():
   ho = "  --- --- ---\n"
   ve = f"| {board[0][0]} | {board[0][1]} | {board[0][2]} |\n"
   ho2 = " --- --- ---\n"
   ve2 = f"| {board[1][0]} | {board[1][1]} | {board[1][2]} |\n"
   ho3 = " --- --- ---\n"
   ve3 = f"| {board[2][0]} | {board[2][1]} | {board[2][2]} |\n"
   ho4 = " --- --- ---\n"
   print(ho, ve, ho2, ve2, ho3, ve3, ho4)
def playX():
    X = input("You are X, enter your move: ")
    if X == "a1" and board[0][0] == 0:
       board[0][0] = 1
    elif X == "b1" and board[0][1] == 0:
       board[0][1] = 1
    elif X == "c1"and board[0][2] == 0:
       board[0][2] = 1
    elif X == "a2" and board[1][0] == 0:
       board[1][0] = 1
    elif X == "b2" and board[1][1] == 0:
       board[1][1] = 1
    elif X == "c2" and board[1][2] == 0:
       board[1][2] = 1
    elif X == "a3" and board[2][0] == 0:
       board[2][0] = 1
    elif X == "b3" and board[2][1] == 0:
       board[2][1] = 1
    elif X == "c3" and board[2][2] == 0:
       board[2][2] = 1
    else:
        print("Invalid move, try again")
        playX()
def playO():
    O = input("You are O, enter your move: ")
    if O == "a1" and board[0][0] == 0:
        board[0][0] = 2
    elif O == "b1" and board[0][1] == 0:
        board[0][1] = 2
    elif O == "c1" and board[0][2] == 0:
        board[0][2] = 2
    elif O == "a2" and board[1][0] == 0:
        board[1][0] = 2
    elif O == "b2" and board[1][1] == 0:
        board[1][1] = 2
    elif O == "c2" and board[1][2] == 0:
        board[1][2] = 2
    elif O == "a3" and board[2][0] == 0:
        board[2][0] = 2
    elif O == "b3" and board[2][1] == 0:
        board[2][1] = 2
    elif O == "c3" and board[2][2] == 0:
        board[2][2] = 2
    else:
        print("Invalid move, try again")
        playO()
def win():
   global winX, winO, gaming
   # Win conditions
   # Horizontal X
   if board[0][0] == board[0][1] == board[0][2] == 1:
       winX = True
       gaming = False
   elif board[1][0] == board[1][1] == board[1][2] == 1:
       winX = True
       gaming = False
   elif board[2][0] == board[2][1] == board[2][2] == 1:
       winX = True
       gaming = False
   # Vertical X
   elif board[0][0] == board[1][0] == board[2][0] == 1:
       winX = True
       gaming = False
   elif board[0][1] == board[1][1] == board[2][1] == 1:
       winX = True
       gaming = False
   elif board[0][2] == board[1][2] == board[2][2] == 1:
       winX = True
       gaming = False
   # Diagonal X
   elif board[0][0] == board[1][1] == board[2][2] == 1:
       winX = True
       gaming = False
   elif board[2][0] == board[1][1] == board[0][2] == 1:
       winX = True
       gaming = False


   # Horizontal O
   elif board[0][0] == board[0][1] == board[0][2] == 2:
       winO = True
       gaming = False
   elif board[1][0] == board[1][1] == board[1][2] == 2:
       winO = True
       gaming = False
   elif board[2][0] == board[2][1] == board[2][2] == 2:
       winO = True
       gaming = False
   # Vertical O
   elif board[0][0] == board[1][0] == board[2][0] == 2:
       winO = True
       gaming = False
   elif board[0][1] == board[1][1] == board[2][1] == 2:
       winO = True
       gaming = False
   elif board[0][2] == board[1][2] == board[2][2] == 2:
       winO = True
       gaming = False
   # Diagonal O
   elif board[0][0] == board[1][1] == board[2][2] == 2:
       winO = True
       gaming = False
   elif board[2][0] == board[1][1] == board[0][2] == 2:
       winO = True
       gaming = False
   return winX, winO, gaming
def game():
   playX()
   print_board()
   win()
   if not gaming:
       print("X wins!")
       return
   playO()
   print_board()
   win()
   if not gaming:
       print("O wins!")


while gaming:
   game()
