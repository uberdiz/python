import random
randnum = random.randint(0, 267750)
def random_word():
    all_words = []
    with open('!words.txt', 'r') as file:
        for line in file.readlines():
            all_words.append(line.strip())
    return all_words[randnum]
word = list(random_word())
gaming = True
won = False
lost = False
# Guesed letters.
wordguess = word.copy()
# word length.
wordcount = len(wordguess)
# Print the current state of the word guesser.
for i in range(0, wordcount):
    wordguess[i] = '_'
miss = 6
letter_list = []
def print_man():
    if miss == 6:
        print("___________\n |      |      \n |      |      \n |      O      \n |     /|\     \n |     / \     ")
    elif miss == 5:
        print("___________\n |      |      \n |      |      \n |      O      \n |     /|\     \n |     /       ")
    elif miss == 4:
        print("___________\n |      |      \n |      |      \n |      O      \n |     /|\     \n |             ")
    elif miss == 3:
        print("___________\n |      |      \n |      |      \n |      O      \n |     /|      \n |             ")
    elif miss == 2:
        print("___________\n |      |      \n |      |      \n |      O      \n |      |      \n |             ")
    elif miss == 1:
        print("___________\n |      |      \n |      |      \n |      O      \n |             \n |             ")
    elif miss == 0:
        print("___________\n |      |      \n |      |      \n |      O      \n |             \n |             \nGame Over!")
def guess_letter():
    global miss
    global won
    global lost
    global gaming
    global letter_list
    print(wordguess)
    print(f"You have already guessed: {' '.join(letter_list)}")
    letter = input("Guess a letter: ").upper()
    letter_list.append(letter)
    if letter in word:
        print(f"Good job, {letter} is in the word!")
        for i in range(0, wordcount):
            if word[i] == letter:
                wordguess[i] = letter
        print(wordguess)
        if wordguess == word:
            won = True
            gaming = False
            print("Congratulations, you won!")
    else:
        print(f"Sorry, {letter} is not in the word.")
        miss -= 1
        print(f"Attempts left: {miss}")
        print(wordguess)
        if miss == 0:
            print(f"Sorry, you lost. The word was {''.join(word)}")
            gaming = False
print("Welcome to Hangman!")
print(f"You have {miss} attempts to guess the word.")
while gaming == True:
    print_man()
    guess_letter()