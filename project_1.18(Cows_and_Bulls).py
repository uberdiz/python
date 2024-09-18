import random
#POV: 3 hours of my time
# Generate a random 4-digit number
num = random.randint(1000, 9999)
numberList = [int(i) for i in str(num)]
print(f"Number to guess: {num}")  # For debugging purposes
counter = 0

# Function to play cows and bulls
def cows_and_bulls():
    cows = 0
    bulls = 0
    guess = str(input("Guess a 4-digit number: "))
    guess_list = [int(i) for i in str(guess)]  # Convert guess into a list of digits
    
    # Copy lists to mark used digits
    num_copy = numberList[:]
    guess_copy = guess_list[:]
    
    # First pass: count cows (correct digit and position)
    for x in range(4):
        if guess_list[x] == numberList[x]:
            cows += 1
            num_copy[x] = -1  # Mark as used
            guess_copy[x] = -2  # Mark as used
    
    # Second pass: count bulls (correct digit, wrong position)
    for x in range(4):
        if guess_copy[x] != -2 and guess_copy[x] in num_copy:
            bulls += 1
            # Mark the matching number as used as to not use it again in the other digits
            num_copy[num_copy.index(guess_copy[x])] = -1

    # Return the number of cows and bulls, and the guess
    return cows, bulls, guess

# Main game loop
while True:
    cows, bulls, guess = cows_and_bulls()
    counter += 1
    print(f"Cows: {cows}, Bulls: {bulls}")
    
    # Check if the guess is correct
    if guess == str(num):
        print(f"You guessed it right in {counter} guesses!")
        break
