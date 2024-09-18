import random
random_number = random.randint(1, 9)
guess = 0
running = True
guess = input("Guess a number between 1 and 9: ")
while running:
    if int(guess) == random_number:
        print("You guessed right!")
        guess = input("Guess a number between 1 and 9: ")
        random_number = random.randint(1, 9)
    elif int (guess) < random_number:
        print("Your guess is too low, try again")
        guess = input("Guess a number between 1 and 9: ")
        random_number = random.randint(1, 9)
    elif int (guess) > random_number:
        print("Your guess is too high, try again")
        guess = input("Guess a number between 1 and 9: ")
        random_number = random.randint(1, 9)
    elif guess.lower() == "exit":
        running = False
    else:
        print("Invalid input, try again")
        guess = input("Guess a number between 1 and 9: ")
        random_number = random.randint(1, 9)