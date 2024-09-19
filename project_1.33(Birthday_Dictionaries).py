import json
'''
with open("BDayList.json", "w") as f:
    json.dump(Birthdays, f)
'''
with open("BDayList.json", "r") as f:
    info = json.load(f)
Birthdays = info
def find_name():
    for x in Birthdays:
        print(x["name"])
    return x["name"]

print("Welcome to the Birthday game ! We have the birthdays to:")
names = find_name()
choice = input("Who's birthday do you want to look up? ")
print(choice)
if choice in names:
    print(f"{choice}'s birthday is: ", Birthdays[{choice}])
elif choice not in names:
    print("Sorry, I don't have the birthday of that person.")
