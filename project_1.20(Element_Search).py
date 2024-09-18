# Write a function that takes an ordered list of numbers (a list where the elements are in order from smallest to largest) and another number. 
# The function decides whether or not the given number is inside the list and returns (then prints) an appropriate boolean.
#Extras:
#Use binary search.
'''
real_password = "unsafepassword"
user_password = input("Enter the password: ")
while user_password != real_password:
    user_password = input("Enter the password: ")
print("You may enter!")
'''

# My solution:
def binary_search():
    ordered_list = [1, 5, 8, 11, 34, 53, 63, 76, 89, 90]
    target_number = int(input("Enter a number: "))
    count = 0
    low = 0
    high = len(ordered_list) - 1

    while low <= high:
        mid = (low + high) // 2
        print(f"Mid: {mid}")

        if ordered_list[mid] == target_number:
            print("Found it!")
            return  # Exit the function as the target is found

        elif ordered_list[mid] > target_number:
            high = mid - 1
            print("Lower")
        else:
            low = mid + 1
            print("Higher")

    print("Not in list.")  # If the loop ends without finding the number

binary_search()
