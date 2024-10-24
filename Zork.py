import random
import time
print("Welcome to Zork!")
time.sleep(.6)
print("You need to collect the Magic Stones to defeat the Boss Monster(Floor 3) and you get the PRIZE the room over!")
time.sleep(2.5)
print("Big hits have large damage potential but could not be very effective ex.(2-15)")
time.sleep(2)
print("Small hits have small damage potential but are more reliable ex.(5-7)")
time.sleep(1.5)
print("Good luck!")
time.sleep(.8)
# 3 Floors with 4 Rooms each
# 5 Floors with 6 Rooms each
f1 = [['UpStairs'], ['Sword', 'Fire Sword', 'Cursed Sword', 'Big Sword', 'Dex Charm', 'Cursed Armor', 'Healing Potion', 'Stamina Potion', 'Ice Shield', 'Thunder Hammer', 'Armor', 'Dex Charm'], ['Monster'], ['Stamina Potion'], ['Monster'], ['Cursed Sword']]
f2 = [['UpStairs'], ['DownStairs', 'Magic Stones'], ['Dex Charm', 'Shield'], ['Monster'], ['Potion'], ['Monster', 'Cursed Armor']]
f3 = [['Monster'], ['DownStairs'], ['Boss', 'Sword'], ['None'], ['Armor', 'Magic Stones'], ['Big Sword', 'Potion']]
f4 = [['UpStairs'], ['DownStairs', 'Magic Charm'], ['Monster', 'Sword'], ['Potion'], ['Dex Charm', 'Monster'], ['Armor']]
f5 = [['Magic Stones'], ['UpStairs'], ['Monster', 'Big Sword'], ['PRIZE', 'Boss'], ['Monster'], ['Dex Charm']]

# Player is spawned into a random room on the first floor
spawn  = random.randint(0, len(f1) - 1)
spawn = 0
spawn_floor = 1
dun_floor = f1
# Use a list to keep track of the user's items. At the beginning of the game it should be empty. A maximum of two items can be held.
inventory = []
def player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory):
    time.sleep(.8)
    stamina = 0
    if "Dex Charm" in inventory:
        stamina = 15
    if "Big Sword" in inventory:
        sword_rangeB -= 5
    stamina += 10
    print(f"Boss health = {Boss_health}, Your health = {player_health}, Your Stamina = {stamina}\n")
    if "Fire Sword" in inventory:
        over = random.randint(1, 10)
        Boss_health -= over
        print(f"Your Fire Sword did {over} damage")
        time.sleep(.8)
    num1 = random.randint(20, 100)
    num2 = random.randint(20, 100)
    num1 = num1 + num2
    play = int(input(f"What is {num1} + {num2}? "))
    if play == num1 + num2:  
        play = input("Big hit or Small hit or Heal (B or S or H): ").capitalize()
        while play != "B" and play != "S" and play != "H":
            print("Invalid")
            play = input("Big hit or Small hit or Heal (B or S or H): ").capitalize()
        num1 = random.randint(1, 10)
        if play == "H":
            print(inventory)
            choice = input("Which item would you like to use? ")
            if choice == "Healing Potion":
                if "Healing Potion" in inventory:
                    player_health += 10
                    inventory.remove("Healing Potion")
                else:
                    time.sleep(.8)
                    print("You don't have any Healing Potions")
            elif choice == "Stamina Potion":
                if "Stamina Potion" in inventory:
                    stamina += 10
                    inventory.remove("Stamina Potion")
                else:
                    time.sleep(.8)
                    print("You don't have any Stamina Potions")
            else:
                time.sleep(.8)
                print("Invalid")
                play = input("Big hit or Small hit (B or S): ").capitalize()
                while play != "B" and play != "S":
                    print("Invalid")
                    play = input("Big hit or Small hit (B or S): ").capitalize()
        if num1 == 1:
            time.sleep(.4)
            print("Critical Hit!")
            Crit = True
        if play == "B":
            hit = sword_rangeB
            samina -= 3
        elif play == "S":
            hit = sword_rangeS
            stamina -= 1
        if stamina <= 0:
            stamina = 0
            time.sleep(.4)
            print("Your stamina is empty!")
            time.sleep(.4)
            print("You have died!")
            gaming = False
            return gaming
        if Crit:
            hit = hit * 2
        else:
            hit = hit
        time.sleep(.8)
        print(f"You hit for {hit} damage!")
        Boss_health -= hit

        return Boss_health
def BossBat(inventory, gaming):
    sword_rangeB = random.randint(2, 15)
    sword_rangeS = random.randint(5, 7)
    Boss_health = 100
    player_health = 100
    if "Sword" or "Cursed Sword" or "Big Sword" in inventory and "Magic Stones" in inventory:
        if "Big Sword" in inventory:
            print("Added 5 damage for Big Sword")
            sword_rangeB += 5
            sword_rangeS += 5
        if "Cursed Armor" in inventory:
            print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
            player_health += 50
            sword_rangeB -= sword_rangeB * .3
            sword_rangeS -= sword_rangeS * .3
        if "Cursed Sword" in inventory:
            print("Added 15 damage for Cursed Sword, Helth is reduced by 40%")
            sword_rangeB += 15
            sword_rangeS += 15
            player_health -= player_health * .4
        if "Armor" in inventory:
            print("Added 25 health for Armor")
            player_health += 25
        if "Fire Sword" in inventory:
            print("Added 7 damage for Fire Sword")
            sword_rangeB += 7
            sword_rangeS += 7
        while Boss_health > 0 and player_health > 0:
            Boss_health, gaming = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
            if gaming == False:
                return gaming
            if "Dex Charm" in inventory:
                print("You are too fast because of the Dex Charm, Get ready to hit harder")
                Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
            if "Ice Shield" in inventory and "Dex Charm" not in inventory:
                print("You stun the enemy because of the Ice Shield, Get ready to hit harder")
                Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
            if "Thunder Hammer" in inventory and "Dex Charm" not in inventory and "Ice Shield" not in inventory:
                print("You are too fast because of the Thunder Hammer, Get ready to hit harder")
                Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
            hit = random.randint(1,20)
            time.sleep(.4)
            print(f"The Boss hit you for {hit} damage!")
            player_health -= hit
    else:
        print("You do not have the Magic Stones or a sword to defeat the Boss")
        gaming = False
        return gaming
    if player_health <= 0:
        time.sleep(.4)
        print("You lost!")
        gaming = False
        return gaming
    if Boss_health <= 0:
        time.sleep(.4)
        print("He died!")
        gaming = True
        return gaming
def MonsterBat(inventory, gaming):
    print("Monster Bat")
    sword_rangeB = random.randint(2, 15)
    sword_rangeS = random.randint(5, 7)
    Boss_health = 50
    player_health = 100
    if "Big Sword" in inventory:
            print("Added 5 damage for Big Sword")
            sword_rangeB += 5
            sword_rangeS += 5
    if "Cursed Armor" in inventory:
            print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
            player_health += 50
            sword_rangeB -= sword_rangeB * .3
            sword_rangeS -= sword_rangeS * .3
    if "Cursed Sword" in inventory:
            print("Added 15 damage for Cursed Sword, Helth is reduced by 40%")
            sword_rangeB += 15
            sword_rangeS += 15
            player_health -= player_health * .4
    if "Armor" in inventory:
            print("Added 25 health for Armor")
            player_health += 25
    if "Fire Sword" in inventory:
            print("Added 7 damage for Fire Sword")
            sword_rangeB += 7
            sword_rangeS += 7
    while Boss_health > 0 and player_health > 0:
        Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
        if "Dex Charm" in inventory:
            Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
        hit = random.randint(1,20)
        time.sleep(.4)
        print(f"The Monster hit you for {hit} damage!")
        player_health -= hit
    if player_health <= 0:
        time.sleep(.4)
        print("You lost!")
        gaming = False
        return gaming
    if Boss_health <= 0:
        time.sleep(.4)
        print("He died!")
        gaming = True
        return gaming
def PoisonBat(inventory, gaming):
    sword_rangeB = random.randint(2, 15)
    sword_rangeS = random.randint(5, 7)
    Boss_health = 60
    player_health = 100
    if "Big Sword" in inventory:
            print("Added 5 damage for Big Sword")
            sword_rangeB += 5
            sword_rangeS += 5
    if "Cursed Armor" in inventory:
            print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
            player_health += 50
            sword_rangeB -= sword_rangeB * .3
            sword_rangeS -= sword_rangeS * .3
    if "Cursed Sword" in inventory:
            print("Added 15 damage for Cursed Sword, Helth is reduced by 40%")
            sword_rangeB += 15
            sword_rangeS += 15
            player_health -= player_health * .4
    if "Armor" in inventory:
            print("Added 25 health for Armor")
            player_health += 25
    if "Fire Sword" in inventory:
            print("Added 7 damage for Fire Sword")
            sword_rangeB += 7
            sword_rangeS += 7
    while Boss_health > 0 and player_health > 0:
        Boss_health, gaming = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
        if gaming == False:
            return gaming
        if "Dex Charm" in inventory:
            print("You are too fast because of the Dex Charm, Get ready to hit harder")
            Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
        if "Ice Shield" in inventory and "Dex Charm" not in inventory:
            print("You stun the enemy because of the Ice Shield, Get ready to hit harder")
            Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
        if "Thunder Hammer" in inventory and "Dex Charm" not in inventory and "Ice Shield" not in inventory:
            print("You are too fast because of the Thunder Hammer, Get ready to hit harder")
            Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
        hit = random.randint(1,20)
        print(f"The Monster hit you for {hit} damage!")
        time.sleep(.4)
        poi = random.randint(1, 10)
        hit += poi
        print(f"Poisoned for {poi} damage!")
        time.sleep(.4)
        print(f"The Monster hit you for {hit} damage!")
        player_health -= hit
    if player_health <= 0:
        time.sleep(.4)
        print("You lost!")
        gaming = False
        return gaming
    if Boss_health <= 0:
        time.sleep(.4)
        print("He died!")
        gaming = True
        return gaming
def IceBat(inventory, gaming):
    skipper = random.randint(1, 10)
    if skipper % 2 == 0:
         skipper = True
    else:
         skipper = False
    sword_rangeB = random.randint(2, 15)
    sword_rangeS = random.randint(5, 7)
    Boss_health = 50
    player_health = 100
    if "Big Sword" in inventory:
            print("Added 5 damage for Big Sword")
            sword_rangeB += 5
            sword_rangeS += 5
    if "Cursed Armor" in inventory:
            print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
            player_health += 50
            sword_rangeB -= sword_rangeB * .3
            sword_rangeS -= sword_rangeS * .3
    if "Cursed Sword" in inventory:
            print("Added 15 damage for Cursed Sword, Helth is reduced by 40%")
            sword_rangeB += 15
            sword_rangeS += 15
            player_health -= player_health * .4
    if "Armor" in inventory:
            print("Added 25 health for Armor")
            player_health += 25
    if "Fire Sword" in inventory:
            print("Added 7 damage for Fire Sword")
            sword_rangeB += 7
            sword_rangeS += 7
    while Boss_health > 0 and player_health > 0:
            if skipper == False:
                Boss_health, gaming = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
                if gaming == False:
                    return gaming
                if "Dex Charm" in inventory:
                    print("You are too fast because of the Dex Charm, Get ready to hit harder")
                    Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
                if "Ice Shield" in inventory and "Dex Charm" not in inventory:
                    print("You stun the enemy because of the Ice Shield, Get ready to hit harder")
                    Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
                if "Thunder Hammer" in inventory and "Dex Charm" not in inventory and "Ice Shield" not in inventory:
                    print("You are too fast because of the Thunder Hammer, Get ready to hit harder")
                    Boss_health = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory)
                hit = random.randint(1,20)
                time.sleep(.4)
                print(f"The Boss hit you for {hit} damage!")
                player_health -= hit
            if skipper == True:
                time.sleep(.4)
                print("You are frozen, you can't hit the monster!")
                hit = random.randint(1,20)
                time.sleep(.4)
                print(f"The Boss hit you for {hit} damage!")
                player_health -= hit
    if player_health <= 0:
        time.sleep(.4)
        print("You lost!")
        gaming = False
        return gaming
    if Boss_health <= 0:
        time.sleep(.4)
        print("He died!")
        gaming = True
        return gaming
def Turn(dun_floor, spawn, spawn_floor, inventory):
    gaming = True
    # Prints the contents of the room
    time.sleep(.4)
    print(dun_floor[spawn])
    # Displays if your options  at the start of each turn
    Options = []
    grabs = []
    if dun_floor[-1] != dun_floor[spawn] and dun_floor[spawn + 1]:
        Options.append("Right")
    if dun_floor[spawn - 1] and spawn - 1 != -1:
        Options.append("Left")
    # Adds all the items in the room to the list
    for i in dun_floor[spawn]:
        if i == "UpStairs":
            Options.append("Up")
        if i == "DownStairs":
            Options.append("Down")
        if i == "Sword":
            Options.append("Grab")
            grabs.append("Sword")
        if i == "Cursed Sword":
            grabs.append("Cursed Sword")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Big Sword":
            grabs.append("Big Sword")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Fire Sword":
            grabs.append("Fire Sword")
            if "Grab" not in Options:
                Options.append("Grab")
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
        if i == "Cursed Armor":
            grabs.append("Cursed Armor")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Ice Shield":
            grabs.append("Ice Shield")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Dex Charm":
            grabs.append("Dex Charm")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Healing Potion":
            grabs.append("Healing Potion")
            if "Grab" not in Options:
                Options.append("Grab")
        if i == "Stamina Potion":
            grabs.append("Stamina Potion")
            if "Grab" not in Options:
                Options.append("Grab")
        if inventory and "Drop" not in Options:
            Options.append("Drop")
        if i == "Monster":
            Options = []
            Options.append("Fight")
        if i == "Poison Monster":
            Options = []
            Options.append("Fight")
        if i == "Ice Monster":
            Options = []
            Options.append("Fight")
        if i == "Boss":
            Options = []
            Options.append("Boss Fight")

    time.sleep(.4)    
    print(f"Options: {Options}\n")
    time.sleep(.4)
    # Player chooses an option
    choice = input("What do you do? ").capitalize()
    while choice not in Options:
        print("Invalid")
        choice = input("What do you do? ").capitalize()
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
        if "Sword" in inventory or "Big Sword" in inventory or "Cursed Sword" in inventory or "Fire Sword" in inventory:
            print(dun_floor[spawn])
            if dun_floor[spawn] == ["Monster"]:
                gaming = MonsterBat(inventory, gaming)
            if dun_floor[spawn] == ["Poison Monster"]:
                gaming = PoisonBat(inventory, gaming)
            if dun_floor[spawn] == ["Ice Monster"]:
                gaming = IceBat(inventory, gaming)
            if gaming == False:
                return dun_floor, spawn, spawn_floor, inventory, gaming
            else:
                dun_floor[spawn].remove("Monster")
        else:
            gaming = False
    if choice == "Boss Fight":
        gaming = BossBat(inventory, gaming)
        if gaming == False:
            return dun_floor, spawn, spawn_floor, inventory, gaming
        else:
            dun_floor[spawn].remove("Boss")
    if "PRIZE" in inventory:
        print("You Win!")
        gaming = False

    for i in range(len(dun_floor)):
        if dun_floor[i] == []:
            dun_floor[i] = ["None"]
    return dun_floor, spawn, spawn_floor, inventory, gaming
gaming = True
while gaming:
    print(f"\nYou are on floor {spawn_floor}, room {spawn + 1}")
    dun_floor, spawn, spawn_floor, inventory, gaming = Turn(dun_floor, spawn, spawn_floor, inventory)
