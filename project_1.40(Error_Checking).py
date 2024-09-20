import random
number = random.randint(1, 9)
number_of_guesses = 0
try:
	guess = int(input("Guess a number between 1 and 9: "))
	print(f"You entered {guess}")
except ValueError:
	print("Not a number.")
while True:
	guess = int(input("Guess a number between 1 and 9: "))
	while guess < 1 or guess > 9:
		print("Not a number between 1 and 9.")
		guess = int(input("Guess a number between 1 and 9: "))
		
	number_of_guesses += 1
	if guess == number:
		break
print(f"You needed {number_of_guesses} guesses to guess the number {number}")
