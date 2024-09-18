board = [[0, 0, 0],
	[0, 0, 0],
	[0, 0, 0]]
winX = False
winO = False
gaming = True
def print_board():
    ho = f" --- --- ---"
    ve = f"| {board[0][0]}  | {board[0][1]}  | {board[0][2]}  |"
    ho2 =f" --- --- ---"
    ve2 = f"| {board[1][0]}  | {board[1][1]}  | {board[1][2]}  |"
    ho3 =f" --- --- ---"
    ve3 = f"| {board[2][0]}  | {board[2][1]}  | {board[2][2]}  |"
    ho4 =f" --- --- ---"
    print(ho,ve,ho2,ve2,ho3,ve3,ho4)
print_board()
def playX():
    X = input("You are X enter your move: ")
    if X == "a1":
        board[0][0] = 1
    elif X == "b1":
        board[0][1] = 1
    elif X == "c1":
        board[0][3] = 1
    elif X == "a2":
        board[1][0] = 1
    elif X == "b2":
        board[1][1] = 1
    elif X == "c2":
        board[1][2] = 1
    elif X == "a3":
        board[2][0] = 1
    elif X == "b3":
        board[2][1] = 1
    elif X == "c3":
        board[2][2] = 1
def playO():
    X = input("You are O enter your move: ")
    if X == "a1":
        board[0][0] = 2
    elif X == "b1":
        board[0][1] = 2
    elif X == "c1":
        board[0][3] = 2
    elif X == "a2":
        board[1][0] = 2
    elif X == "b2":
        board[1][1] = 2
    elif X == "c2":
        board[1][2] = 2
    elif X == "a3":
        board[2][0] = 2
    elif X == "b3":
        board[2][1] = 2
    elif X == "c3":
        board[2][2] = 2
    print_board()
def win():
    # Win condidtions
    # Horizontal X
    if board[0][0] and board[0][1] and board[0][2] == 1:
        winX = True
        gaming = False
    elif board[1][0] and board[1][1] and board[1][2] == 1:
        winX = True
        gaming = False
    elif board[2][0] and board[2][1] and board[2][2] == 1:
        winX = True
        gaming = False
    # Vertical X
    elif board[0][0] and board[1][0] and board[2][0] == 1:
        winX = True
        gaming = False  
    elif board[0][1] and board[1][1] and board[2][1] == 1:
        winX = True
        gaming = False   
    elif board[0][2] and board[1][2] and board[2][2] == 1:
        winX = True
        gaming = False
    # Diagonal X
    elif board[0][0] and board[1][1] and board[2][2] == 1:
        winX = True
        gaming = False  
    elif board[2][2] and board[1][1] and board[0][0] == 1:
        winX = True
        gaming = False


    
    # Horizontal O
    elif board[0][0] and board[0][1] and board[0][2] == 2:
        winO = True
        gaming = False
    elif board[1][0] and board[1][1] and board[1][2] == 2:
        winO = True
        gaming = False
    elif board[2][0] and board[2][1] and board[2][2] == 2:
        winO = True
        gaming = False
    # Vertical O
    elif board[0][0] and board[1][0] and board[2][0] == 2:
        winO = True
        gaming = False  
    elif board[0][1] and board[1][1] and board[2][1] == 2:
        winO = True
        gaming = False   
    elif board[0][2] and board[1][2] and board[2][2] == 2:
        winO = True
        gaming = False
    # Diagonal O
    elif board[0][0] and board[1][1] and board[2][2] == 2:
        winO = True
        gaming = False  
    elif board[2][2] and board[1][1] and board[0][0] == 2:
        winO = True
        gaming = False  
    else: 
        gaming == True
def game():
    playX()
    playO()
    win()
while gaming == True:
    game()
if gaming == False and winX == True:
    print("X wins!")
elif gaming == False and winO == True:
    print("O wins!")