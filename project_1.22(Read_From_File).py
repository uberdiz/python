# Given a .txt file that has a list of a bunch of names, count how many of each name there are in the file, and print out the results to the screen. 
# Open the file in read mode
all_names = {'Lea':0, 'Darth':0, 'Luke':0}
def name_count():
    if x in all_names:
            all_names[x] += 1
with open('name_list.txt', 'r') as file:
    # Loop through each line in the file
    for line in file:
        # Print or process the line
        x = line.strip()  # .strip() removes extra whitespace
        name_count()
print("Number of names:", all_names)