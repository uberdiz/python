def print_verticals(grid_size):
	vertical_string = "|"
	for i in range(grid_size):
		vertical_string += "   |"
	print(vertical_string)

def print_horizontals(grid_size):
	horiz_string = ""
	for i in range(grid_size):
		horiz_string += " ---"
	print(horiz_string)


def print_rectangle():#+
    grid_size_x = int(input("What width would you like the grid to be? "))#+
    grid_size_y = int(input("How high would you like the grid to be? "))#+
    print_horizontals(grid_size_x)#+
    for i in range(grid_size_y):#+
        print_verticals(grid_size_x)#+
        print_horizontals(grid_size_x)#+




choice = input("What would you like to do, square or rectangle? ")
while choice != "square" and choice != "rectangle":
    choice = input("What would you like to do, square or rectangle? ")
if choice == "square":
    grid_size = int(input("What size would you like the grid to be? "))
    print_horizontals(grid_size)
    for i in range(grid_size):
        print_verticals(grid_size)
        print_horizontals(grid_size)
elif choice == "rectangle":
    print_rectangle()
