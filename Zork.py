import random
import time
print("Welcome to Zork!")
time.sleep(.6)
print("You need to collect the Magic Stones to defeat the Boss Monster(Floor 5) and you get the PRIZE the room over!")
time.sleep(2.5)
print("Big hits have large damage potential but could not be very effective ex.(2-15)")
time.sleep(2)
print("Small hits have small damage potential but are more reliable ex.(5-7)")
time.sleep(1.5)
print("Good luck!")
time.sleep(.8)
# 5 Floors with 6 Rooms each
f1 = [['None'], 
      ['Sword', 'Healing Potion', 'Armor'], 
      ['Monster'], 
      ['Stamina Potion'], 
      ['Ice Monster'], 
      ['Dex Charm', 'Cursed Sword', 'UpStairs']] 
f2 = [['UpStairs'], 
      ['DownStairs', 'Magic Stones'], 
      ['Ice Shield', 'Stamina Potion'], 
      ['Monster', 'Cursed Armor'], 
      ['Monster'], 
      ['Dex Charm']] 
f3 = [['DownStairs'], 
      ['Poison Monster'], 
      ['Armor', 'Magic Stones'], 
      ['UpStairs'],  
      ['Monster'], 
      ['Big Sword']] 
f4 = [['UpStairs'], 
      ['DownStairs', 'Magic Charm'], 
      ['Monster', 'Sword'], 
      ['Healing Potion', 'Armor'], 
      ['Dex Charm', 'Monster'], 
      ['Healing Potion']] 
f5 = [['Magic Stones'], 
      ['DownStairs'], 
      ['Monster', 'Big Sword'], 
      ['Boss'],  # The Boss Room
      ['PRIZE'],  # PRIZE is one room over from the Boss
      ['Monster']]


# Player is spawned into a random room on the first floor
spawn = 0
spawn_floor = 1
dun_floor = f1
# Use a list to keep track of the user's items. At the beginning of the game it should be empty. A maximum of two items can be held.
inventory = []
def player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina):
    
    Crit = False
    time.sleep(.8)

    print(f"Boss health = {Boss_health}, Your health = {player_health}, Your Stamina = {stamina}\n")
    
    # Fire Sword bonus damage
    if "Fire Sword" in inventory:
        over = random.randint(1, 10)
        Boss_health -= over
        print(f"Your Fire Sword did {over} damage")
        time.sleep(.8)

    # Math challenge for attack
    num1 = random.randint(20, 50)
    num2 = random.randint(20, 50)
    play = int(input(f"What is {num1} + {num2}? "))
    
    # Ensure correct math input from player
    if play == num1 + num2:  
        play = input("Big hit or Small hit or Heal (B or S or H): ").lower()
        while play not in ["b", "s", "h"]:
            print("Invalid")
            play = input("Big hit or Small hit or Heal (B or S or H): ").lower()

        # Healing logic
        if play == "h":
            print(inventory)
            choice = input("Which item would you like to use? ").lower()
            if choice == "healing potion" and "Healing Potion" in inventory:
                player_health += 10
                print("Health restored + 10")
                inventory.remove("Healing Potion")
            elif choice == "stamina potion" and "Stamina Potion" in inventory:
                stamina += 10
                print("Stamina restored + 10")
                inventory.remove("Stamina Potion")
            else:
                print("You don't have that potion.")
            return Boss_health, stamina

        # Critical hit logic
        if random.randint(1, 5) == 1:
            print("Critical Hit!")
            Crit = True

        # Attack logic
        hit = sword_rangeB if play == "b" else sword_rangeS
        stamina -= 3 if play == "b" else 1
        if Crit:
            hit = hit * 2
        
        print(f"You hit for {hit} damage!")
        Boss_health -= hit
    else:
        print("You missed!")
        return Boss_health, stamina
    return Boss_health, stamina
def BossBat(inventory, gaming):
    Boss_health = 200
    player_health = 100
    
    if "Sword" in inventory or "Cursed Sword" in inventory or "Big Sword" in inventory or "Thunder Hammer" in inventory or "Fire Sword" in inventory and "Magic Stones" in inventory:
        # Initial adjustments for weapons and armor
        if "Big Sword" in inventory:
            big_sword_bonus = 5
        else:
            big_sword_bonus = 0
        
        if "Cursed Armor" in inventory:
            print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
            player_health += 50
            damage_modifier = 0.7  # Reduce damage by 30%
        else:
            damage_modifier = 1.0
            
        if "Cursed Sword" in inventory:
            print("Added 15 damage for Cursed Sword, Health is reduced by 40%")
            cursed_sword_bonus = 15
            player_health *= 0.6  # Reduce health by 40%
        else:
            cursed_sword_bonus = 0
            
        if "Fire Sword" in inventory:
            print("Added 7 damage for Fire Sword")
            fire_sword_bonus = 7
        else:
            fire_sword_bonus = 0
            
        if "Thunder Hammer" in inventory:
            print("Added 5 damage for Thunder Hammer")
            thunder_hammer_bonus = 5
        else:
            thunder_hammer_bonus = 0
        
        if "Ice Shield" in inventory:
            print("Added 10 health for Ice Shield")
            player_health += 10
        if "Armor" in inventory:
            print("Added 5 health for Armor")
            player_health += 5
            
        stamina = 35 if "Dex Charm" in inventory else 25
        
        # Main game loop
        while Boss_health > 0 and player_health > 0 and stamina > 0:
            # Update damage range each turn
            sword_rangeB = random.randint(2, 15) + big_sword_bonus + cursed_sword_bonus + fire_sword_bonus + thunder_hammer_bonus
            sword_rangeS = random.randint(5, 7) + big_sword_bonus + cursed_sword_bonus + fire_sword_bonus + thunder_hammer_bonus
            sword_rangeB = int(sword_rangeB * damage_modifier)
            sword_rangeS = int(sword_rangeS * damage_modifier)
            
            # Player attacks boss
            Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)
            if not gaming:
                return False
            
            # Handle effects like Dex Charm
            if "Dex Charm" in inventory:
                print("You are too fast because of the Dex Charm, get ready to hit harder")
                Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)
            elif "Ice Shield" in inventory or "Thunder Hammer" in inventory:
                print("You are too fast, get ready to hit harder")
                Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)
            
            # Monster retaliation
            hit = random.randint(5, 15)
            print(f"The Boss hit you for {hit} damage!")
            player_health -= hit

        if player_health <= 0:
            print("You lost!")
            return False
        if Boss_health <= 0:
            print("The Boss is defeated!")
            return True
    else:
        print("You don't have the necessary items to fight the Boss.")
        return False
def MonsterBat(inventory, gaming):
    stamina = 35 if "Dex Charm" in inventory else 25
    Boss_health = 50
    player_health = 100

    # Apply inventory-based adjustments once, outside the loop
    sword_damage_bonus_B = sword_damage_bonus_S = 0
    if "Big Sword" in inventory:
        print("Added 5 damage for Big Sword")
        sword_damage_bonus_B += 5
        sword_damage_bonus_S += 5
    if "Cursed Armor" in inventory:
        print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
        player_health += 50
        sword_damage_bonus_B *= 0.7  # Reduce damage by 30%
        sword_damage_bonus_S *= 0.7
    if "Cursed Sword" in inventory:
        print("Added 15 damage for Cursed Sword, Health is reduced by 40%")
        sword_damage_bonus_B += 15
        sword_damage_bonus_S += 15
        player_health *= 0.6  # Reduce health by 40%
    if "Fire Sword" in inventory:
        print("Added 7 damage for Fire Sword")
        sword_damage_bonus_B += 7
        sword_damage_bonus_S += 7
    if "Thunder Hammer" in inventory:
        print("Added 5 damage for Thunder Hammer")
        sword_damage_bonus_B += 5
        sword_damage_bonus_S += 5
    if "Ice Shield" in inventory:
        print("Added 10 health for Ice Shield")
        player_health += 10
    if "Armor" in inventory:
        print("Added 5 health for Armor")
        player_health += 5

    # Main loop for combat
    while Boss_health > 0 and player_health > 0 and stamina > 0:
        # Randomize sword range on each hit
        sword_rangeB = random.randint(2, 15) + sword_damage_bonus_B
        sword_rangeS = random.randint(5, 7) + sword_damage_bonus_S

        Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)
        if not gaming:
            return False

        # Extra attack logic if Dex Charm or other inventory items are present
        if "Dex Charm" in inventory or "Ice Shield" in inventory or "Thunder Hammer" in inventory:
            print("You are too fast due to a charm or shield effect, get ready to hit harder")
            sword_rangeB = random.randint(2, 15) + sword_damage_bonus_B
            sword_rangeS = random.randint(5, 7) + sword_damage_bonus_S
            Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)

        # Monster retaliation
        hit = random.randint(1, 10)
        print(f"The Boss hit you for {hit} damage!")
        player_health -= hit

    # Outcome
    if player_health <= 0:
        print("You lost!")
        return False
    if Boss_health <= 0:
        print("You won!")
        return True
def PoisonBat(inventory, gaming):
    Boss_health = 60
    player_health = 100
    
    # Modify player stats based on inventory items
    if "Big Sword" in inventory:
        print("Added 5 damage for Big Sword")
        base_sword_rangeB = 5
        base_sword_rangeS = 5
    else:
        base_sword_rangeB = 0
        base_sword_rangeS = 0
    if "Cursed Armor" in inventory:
        print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
        player_health += 50
        base_sword_rangeB *= 0.7  # Reduce damage by 30%
        base_sword_rangeS *= 0.7
    if "Cursed Sword" in inventory:
        print("Added 15 damage for Cursed Sword, Health is reduced by 40%")
        base_sword_rangeB += 15
        base_sword_rangeS += 15
        player_health *= 0.6  # Reduce health by 40%
    if "Fire Sword" in inventory:
        print("Added 7 damage for Fire Sword")
        base_sword_rangeB += 7
        base_sword_rangeS += 7
    if "Thunder Hammer" in inventory:
        print("Added 5 damage for Thunder Hammer")
        base_sword_rangeB += 5
        base_sword_rangeS += 5
    if "Ice Shield" in inventory:
        print("Added 10 health for Ice Shield")
        player_health += 10
    if "Armor" in inventory:
        print("Added 5 health for Armor")
        player_health += 5
    stamina = 35 if "Dex Charm" in inventory else 25

    # Start the battle loop
    while Boss_health > 0 and player_health > 0 and stamina > 0:
        # Generate new random sword ranges for each hit
        sword_rangeB = random.randint(2, 15) + base_sword_rangeB
        sword_rangeS = random.randint(5, 7) + base_sword_rangeS

        # Player hits the boss
        Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)
        
        if not gaming:
            return False

        # Handle effects of Dex Charm
        if "Dex Charm" in inventory:
            print("You are too fast because of the Dex Charm, get ready to hit harder")
            Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)

        # Monster retaliation
        hit = random.randint(2, 10)
        print(f"The Boss hit you for {hit} damage!")
        player_health -= hit

    if player_health <= 0:
        print("You lost!")
        return False
    if Boss_health <= 0:
        print("The Poison Monster is defeated!")
        return True
def IceBat(inventory, gaming):
    skipper = random.randint(1, 10)
    if skipper % 4 == 0:
        skipper = True
    else:
        skipper = False

    Boss_health = 50
    player_health = 100

    if not skipper:
        # Modify stats based on inventory
        if "Big Sword" in inventory:
            print("Added 5 damage for Big Sword")
            extra_damage = 5
        else:
            extra_damage = 0

        if "Cursed Armor" in inventory:
            print("Added 50 health for Cursed Armor, Damage is reduced by 30%")
            player_health += 50
            damage_reduction = 0.7
        else:
            damage_reduction = 1

        if "Cursed Sword" in inventory:
            print("Added 15 damage for Cursed Sword, Health is reduced by 40%")
            player_health *= 0.6
            extra_damage += 15

        if "Fire Sword" in inventory:
            print("Added 7 damage for Fire Sword")
            extra_damage += 7

        if "Thunder Hammer" in inventory:
            print("Added 5 damage for Thunder Hammer")
            extra_damage += 5

        if "Ice Shield" in inventory:
            print("Added 10 health for Ice Shield")
            player_health += 10

        if "Armor" in inventory:
            print("Added 5 health for Armor")
            player_health += 5

        stamina = 35 if "Dex Charm" in inventory else 25

        # Combat loop
        while Boss_health > 0 and player_health > 0 and stamina > 0:
            # Generate new sword ranges for each hit
            sword_rangeB = random.randint(2, 15) + extra_damage
            sword_rangeS = random.randint(5, 7) + extra_damage
            sword_rangeB *= damage_reduction
            sword_rangeS *= damage_reduction

            # Player hits the Boss
            Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)
            if not gaming:
                return False

            # Special inventory effects
            if "Dex Charm" in inventory:
                print("You are too fast because of the Dex Charm, get ready to hit harder")
                Boss_health, stamina = player_hit(sword_rangeB, sword_rangeS, Boss_health, player_health, gaming, inventory, stamina)

            # Monster retaliation
            hit = random.randint(1, 10)
            print(f"The Boss hit you for {hit} damage!")
            player_health -= hit

    elif skipper:
        print("The Ice Monster froze you!")
        hit = random.randint(1, 20)
        print(f"The Boss hit you for {hit} damage!")
        player_health -= hit

    if player_health <= 0:
        print("You lost!")
        return False
    if Boss_health <= 0:
        print("The Ice Monster is defeated!")
        return True
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

                                    #Grabs
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
        if i == "Thunder Hammer":
            grabs.append("Thunder Hammer")
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
    for i in range(0, len(Options)):
        Options[i] = Options[i].lower()
    time.sleep(.4)
    # Player chooses an option
    choice = input("What do you do? ").lower()
    while choice not in Options:
        print("Invalid")
        choice = input("What do you do? ").lower()
    if choice != "fight" and "monster" in dun_floor[spawn] or "poison monster" in dun_floor[spawn] or "ice monster" in dun_floor[spawn] or "boss" in dun_floor[spawn]:
        gaming = False
    if choice == "right":
        spawn += 1
    if choice == "left":
        spawn -= 1
    if choice == "up":
        spawn_floor += 1
        if spawn_floor == 1:
            dun_floor = f1
        if spawn_floor == 2:
            dun_floor = f2
        if spawn_floor == 3:
            dun_floor = f3
        if spawn_floor == 4:
            dun_floor = f4
        if spawn_floor == 5:
            dun_floor = f5
    if choice == "down":
        spawn_floor -= 1
        if spawn_floor == 1:
            dun_floor = f1
        if spawn_floor == 2:
            dun_floor = f2
        if spawn_floor == 3:
            dun_floor = f3
        if spawn_floor == 4:
            dun_floor = f4
        if spawn_floor == 5:
            dun_floor = f5
    if choice == "grab":
        if len(inventory) < 4:
            print(grabs)
            grabs = [item.lower() for item in grabs]   
            grabbed = input("What do you grab (All for every item)? ").lower()       
            while grabbed not in grabs and grabbed != "all":
                print("Invalid")
                grabbed = input("What do you grab (All for every item)? ").lower()    
            if grabbed != "all":   
                grabbed = grabbed.split()    
                if len(grabbed) > 1:
                    var = [word.capitalize() for word in grabbed]  
                    grabbed = " ".join(var)
                else:
                    grabbed = grabbed[0].capitalize() 
                inventory.append(grabbed) 
                dun_floor[spawn].remove(grabbed)
                grabs = [item.capitalize() for item in grabs]
            else:  # All
                dun_floor[spawn] = [item.lower() for item in dun_floor[spawn]] 
                for item in grabs:
                    words = item.split()
                    if len(words) > 1:
                        capitalized_item = " ".join([word.capitalize() for word in words])
                        inventory.append(capitalized_item)
                    else:
                        item = item.capitalize()
                        inventory.append(item)
                    lower_item = item.lower()
                    if lower_item in dun_floor[spawn]:
                        dun_floor[spawn].remove(lower_item)
        else:
            print("Inventory is full.")
    if choice == "drop":
        print(inventory)
        inventory = [item.lower() for item in inventory]
        dropped = input("What do you drop? ").lower()
        while dropped not in inventory:
            print("Invalid")
            dropped = input("What do you drop? ").lower()
        dropped = dropped.split()
        if len(dropped) > 1:
            dropped = " ".join([word.capitalize() for word in dropped])
        else:
            dropped = dropped[0].capitalize()
        inventory = [item.capitalize() for item in inventory if item != dropped.lower()]
        dun_floor[spawn].append(dropped)
        if len(dun_floor[spawn]) >= 2:
            dun_floor[spawn].remove("None")
    if choice == "fight":
        if "Sword" in inventory or "Big Sword" in inventory or "Cursed Sword" in inventory or "Fire Sword" in inventory or "Thunder Hammer" in inventory:
            if "Monster" in dun_floor[spawn]:
                gaming = PoisonBat(inventory, gaming)
                mon = "Monster"
            if "Poison Monster" in dun_floor[spawn]:
                gaming = PoisonBat(inventory, gaming)
                mon = "Poison Monster"
            if "Ice Monster" in dun_floor[spawn]:
                gaming = PoisonBat(inventory, gaming)
                mon = "Ice Monster"
            if gaming == False:
                return dun_floor, spawn, spawn_floor, inventory, gaming
            else:
                dun_floor[spawn].remove(mon)
        else:
            gaming = False
    if choice == "boss fight":
        gaming = BossBat(inventory, gaming)
        if gaming == False:
            return dun_floor, spawn, spawn_floor, inventory, gaming
        else:
            dun_floor[spawn].remove("Boss")
    if "prize" in inventory:
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
