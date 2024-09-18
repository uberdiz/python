# a does not have to be specified here yet because the functions below do not use it yet.
a = [1, 2, 3, 4, 5, 3, 2, 6, 7, 5]
# a in the function below is the argument and does not have to be the same as the list.
def remove_dupes(a):
    # y is a new list.
    y = []
    # iterate over the original list and add unique elements to y list.
    for x in a:
        if x not in y:
            y.append(x)
    # return the new list with unique elements
    return y
def remove_dupesv2(a):
    # Changes the list to a set to find the unique elements.
    return list(set(a))
# Testing the function.
print(remove_dupes(a))
print(remove_dupesv2(a))