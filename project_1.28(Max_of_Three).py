# Implement a function that takes as input three variables, and returns the largest of the three. 
# Do this without using the Python max() function!
# The goal of this exercise is to think about some internals that Python normally takes care of for us. 
# All you need is some variables and if statements!
def find_largest():
    # Make a list of the three variables and use the .max() function to find the largest one.
    var1 = input("Enter the first number: ")
    var2 = input("Enter the second number: ")
    var3 = input("Enter the third number: ")
    input_list = [var1, var2, var3]
    print(max(input_list), "is the largest number.")
find_largest()