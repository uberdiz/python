import json
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
counter = 0
for person in Birthdays:
    if person["name"] == choice:
        print(f"{choice}'s birthday is:", person["age"])
        counter += 1
if counter == 0:
    print("No birthday found")
    yn = input("Do you want to add a birthday? (y/n) ").lower()
    if yn == "y":
        new_age = input("What is their birthday? ")
        new_name = input("What is their name? ")
        Birthdays.append({"name": new_name, "age": new_age})
        with open("BDayList.json", "w") as f:
            json.dump(Birthdays, f)
        print("Birthday added")
    else:
        print("Goodbye")

