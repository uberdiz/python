board = [[" ", " ", " "],
        [" ", " ", " "],
        [" ", " ", " "]]
winX = False
winO = False
gaming = True
print("Welcome to Tic-Tac-Toe\n")
print("a1 | b1 | c1\n---|----|---\na2 | b2 | c2\n---|----|---\na3 | b3 | c3\n")

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
    if X == "a1" and board[0][0] == " ":
       board[0][0] = "X"
    elif X == "b1" and board[0][1] == " ":
       board[0][1] = "X"
    elif X == "c1"and board[0][2] == " ":
       board[0][2] = "X"
    elif X == "a2" and board[1][0] == " ":
       board[1][0] = "X"
    elif X == "b2" and board[1][1] == " ":
       board[1][1] = "X"
    elif X == "c2" and board[1][2] == " ":
       board[1][2] = "X"
    elif X == "a3" and board[2][0] == " ":
       board[2][0] = "X"
    elif X == "b3" and board[2][1] == " ":
       board[2][1] = "X"
    elif X == "c3" and board[2][2] == " ":
       board[2][2] = "X"
    else:
        print("Invalid move, try again")
        playX()
def playO():
    O = input("You are O, enter your move: ")
    if O == "a1" and board[0][0] == " ":
        board[0][0] = "O"
    elif O == "b1" and board[0][1] == " ":
        board[0][1] = "O"
    elif O == "c1" and board[0][2] == " ":
        board[0][2] = "O"
    elif O == "a2" and board[1][0] == " ":
        board[1][0] = "O"
    elif O == "b2" and board[1][1] == " ":
        board[1][1] = "O"
    elif O == "c2" and board[1][2] == " ":
        board[1][2] = "O"
    elif O == "a3" and board[2][0] == " ":
        board[2][0] = "O"
    elif O == "b3" and board[2][1] == " ":
        board[2][1] = "O"
    elif O == "c3" and board[2][2] == " ":
        board[2][2] = "O"
    else:
        print("Invalid move, try again")
        playO()
def win():
   global winX, winO, gaming
   # Win conditions
   # Horizontal X
   if board[0][0] == board[0][1] == board[0][2] == "X":
       winX = True
       gaming = False
   elif board[1][0] == board[1][1] == board[1][2] == "X":
       winX = True
       gaming = False
   elif board[2][0] == board[2][1] == board[2][2] == "X":
       winX = True
       gaming = False
   # Vertical X
   elif board[0][0] == board[1][0] == board[2][0] == "X":
       winX = True
       gaming = False
   elif board[0][1] == board[1][1] == board[2][1] == "X":
       winX = True
       gaming = False
   elif board[0][2] == board[1][2] == board[2][2] == "X":
       winX = True
       gaming = False
   # Diagonal X
   elif board[0][0] == board[1][1] == board[2][2] == "X":
       winX = True
       gaming = False
   elif board[2][0] == board[1][1] == board[0][2] == "X":
       winX = True
       gaming = False


   # Horizontal O
   elif board[0][0] == board[0][1] == board[0][2] == "O":
       winO = True
       gaming = False
   elif board[1][0] == board[1][1] == board[1][2] == "O":
       winO = True
       gaming = False
   elif board[2][0] == board[2][1] == board[2][2] == "O":
       winO = True
       gaming = False
   # Vertical O
   elif board[0][0] == board[1][0] == board[2][0] == "O":
       winO = True
       gaming = False
   elif board[0][1] == board[1][1] == board[2][1] == "O":
       winO = True
       gaming = False
   elif board[0][2] == board[1][2] == board[2][2] == "O":
       winO = True
       gaming = False
   # Diagonal O
   elif board[0][0] == board[1][1] == board[2][2] == "O":
       winO = True
       gaming = False
   elif board[2][0] == board[1][1] == board[0][2] == "O":
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
