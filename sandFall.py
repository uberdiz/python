# Class Example: Sand
# Different Objects from this class: [0,1] [0,2] [0,3] Positions
# Two Attributes: X, Y Positions. If space below is empty, fall. Size
# Method: .add(), .change()

class Sand:
    def __init__(self, coords, size, board):
        self.coords = coords
        self.size = size
        self.board = board
    def perTick(self):
        if self.board[self.coords[0]][self.coords[1] - 1] != None:
            print("smthing below")

def makeBoard(size=5):
    board = []
    for i in range(size):
        board.append([])
        for j in range(size):
            board[i].append([])
    return board

board = makeBoard(5)
sand1 = Sand([0,0], 1, board)
sand2 = Sand([0,1], 1, board)
print(sand2.perTick)

[[[], [], [], [], []],
 [[], [], [], [], []],
 [[], [], [], [], []],
 [[], [], [], [], []],
 [[], [], [], [], []]]
