num = int(input("Pick a number for the computer to guess between 1-100: "))

def find_num():
    guess = 100
    guessing = True
    while guessing == True:
        HL = input(f"Is {guess} higher or lower or equal to your number: ")
        HL.strip()
        HL.lower()
        def higher_lower(HL, guess):
            if HL == "lower":
                guess = guess // 2
            elif HL == "higher":
                guess = guess * 2
            elif HL == "equal":
                print(f"Found it!!! {guess} = {num}")
                guessing = False
            return guess 
        guess = higher_lower(HL, guess)
        higher_lower(HL, guess)
find_num()
