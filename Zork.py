# User can move up or down if the room has a up or down staircase
# The game prints out the contents of the current room after every command.
# The user can grab swords or magic stones if they walk into a room with them. The sword or stones are no longer in the room once grabbed.
# Monsters guard some rooms. 
# The user can use a sword to defeat a monster using the fight command. 
# The monster disappear after fighting. If the user fights without a sword, they will be defeated and the game will end. 
# If they try to walk past a monster, they will be killed and the game will end.
# A sword and magic stones are required to defeat the boss monster.


import random
# 3 Floors with 4 Rooms each
f1 = [['None'], ['Sword'], ['3'], ['Armor']]
f2 = [['UpStairs'], ['DownStairs'], ['None'], ['Magic Stones']]
f3 = [['Monster'], ['DownStairs'], ["Boss"], ['PRIZE']]
# Player is spawned into a random room on the first floor
spawn  = random.randint(0, len(f1) - 1)
spawn = 0
spawn_floor = 1
dun_floor = f1
# Use a list to keep track of the user's items. At the beginning of the game it should be empty. A maximum of two items can be held.
inventory = []

def BossBat(inventory, gaming):
    Boss_health = 100
    player_health = 100
    if "Armor" in inventory:
        print("Added 25 health for Armor")
        player_health += 25
    if "Sword" and "Magic Stones" in inventory:
        while Boss_health > 0 and player_health > 0:
            print(f"Boss health = {Boss_health}, Your health = {player_health}")
            play = input("Big hit(2-15) or Small hit(5-7)(B or S): ")
            while play != "B" and play != "S":
                print("Invalid")
                play = input("Big hit(2-15) or Small hit(5-7)  (B or S): ")
            if play == "B":
                hit = random.randint(2, 16)
            elif play == "S":
                hit = random.randint(5, 8)
            print(f"You hit for {hit} damage!")
            Boss_health -= hit
            hit = random.randint(1,20)
            print(f"The Boss hit you for {hit} damage!")
            player_health -= hit
    if player_health <= 0:
        print("You lost!")
        gaming = False
        return gaming
    if Boss_health <= 0:
        print("He died!")
        gaming = True
        return gaming
def Turn(dun_floor, spawn, spawn_floor, inventory):
    gaming = True
    # Prints the contents of the room for Debuggggggggggggggggggggggggggggggg
    print(dun_floor[spawn])
    # Displays if your options  at the start of each turn
    Options = []
    grabs = []
    if dun_floor[-1] != dun_floor[spawn] and dun_floor[spawn + 1]:
        Options.append("Right")
    if dun_floor[spawn - 1] and spawn - 1 != -1:
        Options.append("Left")
    for i in dun_floor[spawn]:
        if i == "UpStairs":
            Options.append("Up")
        if i == "DownStairs":
            Options.append("Down")
        if i == "Sword":
            Options.append("Grab")
            grabs.append("Sword")
        if i == "Magic Stones":
            grabs.append("Magic Stones")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "PRIZE":
            grabs.append("PRIZE")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Armor":
            grabs.append("Armor")
            if "Grab" not in Options:
                Options.append("Grab")
        if inventory and "Drop" not in Options:
            Options.append("Drop")
        if i == "Monster":
            Options.append("Fight")
        if i == "Boss":
            gaming = BossBat(inventory, gaming)
    print(Options)
    choice = input("What do you do? ").capitalize()
    while choice not in Options:
        print("Invalid")
        choice = input("What do you do? ")
    if choice != "Fight" and "Monster" in dun_floor[spawn]:
        gaming = False
    if choice == "Right":
        spawn += 1
    if choice == "Left":
        spawn -= 1
    if choice == "Up":
        spawn_floor += 1
        if spawn_floor == 1:
            dun_floor = f1
        if spawn_floor == 2:
            dun_floor = f2
        if spawn_floor == 3:
            dun_floor = f3
    if choice == "Down":
        spawn_floor -= 1
        if spawn_floor == 1:
            dun_floor = f1
        if spawn_floor == 2:
            dun_floor = f2
        if spawn_floor == 3:
            dun_floor = f3
    if choice == "Grab":
        if len(inventory) == 3:
            print("Too Many Items")
        elif len(inventory) < 3:
            print(grabs)
            grabbed = input("What do you grab? ")
            while grabbed not in grabs:
                print("Invalid")
                grabbed = input("What do you grab? ")
            inventory.append(grabbed)
            dun_floor[spawn].remove(grabbed)
    if choice == "Drop":
        print(inventory)
        dropped = input("What do you drop? ")
        while dropped not in inventory:
            print("Invalid")
            dropped = input("What do you drop? ")
        inventory.remove(dropped)
        dun_floor[spawn].append(dropped)
    if choice == "Fight":
        if "Sword" in inventory:
            dun_floor[spawn].remove("Monster")
        else:
            gaming = False
    if "PRIZE" in inventory:
        print("You Win!")
        gaming = False
    return dun_floor, spawn, spawn_floor, inventory, gaming
gaming = True
while gaming:
    print(f"You are on floor {spawn_floor}, room {spawn + 1}")
    dun_floor, spawn, spawn_floor, inventory, gaming = Turn(dun_floor, spawn, spawn_floor, inventory)