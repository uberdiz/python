def draw_7():
    for i in range(7):
        print("* * * * * * *")
def stars_and_stripes():
    for i in range(6):
        if i % 2 == 0:
            print("* * * * * * *")
        else:
            print("- - - - - - -")
def increasing_triangle():
    triangle = ""
    for i in range(7):
        if i != 1:
            triangle += f" {i}"
        else:
            triangle = "1"
        print(triangle)
def vertical_stars_and_stripes():
    rows = 6
    cols = 7
    for i in range(rows):
        for j in range(cols):
            if j % 2 == 0:
                print("-", end="")
            else:
                print(" * ", end="")
        print("")
def border():
    rows = 8
    cols = 8
    for i in range(rows):
        if i == 0 or i == rows - 1:
            print("* * * * * * * *", end="")
        else:
            for j in range(cols): # * - - - - - - *
                if j != 0 and j != cols - 1:
                    print(" -", end="")
                elif j == 0:
                    print("*", end="")
                else:
                    print(" *", end="")
        print("")
def balanced_triangle():
    triangle = ""
    targetNum = 7
    for i in range(targetNum * 2):
        if i <= 7:
            if i != 1:
                triangle += f" {i}"
            else:
                triangle = "1"
            print(triangle)
        else:
            triangle = triangle[:-2]
            print(triangle)
'''
   *
  ***
 *****
'''
def cool_triangle():
    width = 5
    height = width - 2
    start, end = 0, 0
    triangle = ""
    for i in range(height):
        start = width // (2+i)
        if start <= 0:
            start = 0
        if start != 0:
            end = start + i * 2
        else:
            end = width
        if i != 0:
            start -= i
        for j in range(width):
            if j <= start or (j > end):
                print(" ", end="")
            elif j == start or (j > start and j < end):
                print("*", end="")
        print("")
cool_triangle()