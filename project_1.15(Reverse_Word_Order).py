# Write a program (using functions!) that asks the user for a long string containing multiple words. Print back to the user the same string, except with the words in backwards order.
teststring = "this is a test"
result = teststring.split("t")
print(result)
teststring = "this i s a t e s t"
result = teststring.split()
print(result)
listofstrings = ['a', 'b', 'c']
result = "**".join(listofstrings)
print(result)
# My solution
def reverseString(string):
    string.split()
    reversedString = string.split()[::-1]
    # could have added [::-1] to the join statment, but I prefer this way
    return " ".join(reversedString)
teststring = input("Give me a sentence with multiple words and it will be reversed: ")
print(reverseString(teststring))