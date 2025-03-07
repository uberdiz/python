class GameVars():
    def __init__(self):
        self.board = None
        self.pieces = ["P", "B", "N", "R", "Q", "K"]
        self.units = {
            "cols": ["A", "B", "C", "D", "E", "F", "G", "H"], 
            "rows": ["1", "2", "3", "4", "5", "6", "7", "8"]
            }
        self.curr = []
def make_board(game):
    for i in game.units["cols"]:
        game.curr.append([])
        for j in game.units["rows"]:
            print("[] ", end="")
            game.curr[game.units["rows"].index(i)].append("[]")
            if j == "2" or "7":
                game.curr[game.units["rows"].index(i)] = "[P]"
            if j == "7":

        print("")
def make_pieces(game):
    for i in game.units["cols"]:
        for j in game.units["rows"]:
            if j == "2":

            


game = GameVars()
make_board(game)
