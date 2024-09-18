size = int(input("How big do you want the board to be:"))
def drawboard(size):
    size = int(size)
    i = 0
    ho = " ---"
    ve = "|   "
    ho = ho * size
    ve = ve * (size+1)
    while i < size+1:
        print (ho)
        if not (i == size):
            print (ve)
        i += 1
drawboard(size)
    