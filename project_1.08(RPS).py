import sys

user1 = input("What is your name? ")
user2 = input("And what is your name? ")
user1_answer = input(user1 + ", do you want to be Rock, Paper or Scissors? ")
while user1_answer != "Rock" and user1_answer != "Paper" and user1_answer != "Scissors":
    user1_answer = input(user1 + ", do you want to be Rock, Paper or Scissors? ")
user2_answer = input(user2 + ", do you want to be Rock, Paper or Scissors? ")
while user2_answer != "Rock" and user2_answer != "Paper" and user2_answer != "Scissors":
    user2_answer = input(user2 + ", do you want to be Rock, Paper or Scissors? ")

def win(u1, u2):
    if u1 == u2:
        return("Tie")
    elif u1 == "Rock":
        if u2 == "Scissors":
            return(user1 + " wins")
        else:
            return(user2 + " wins")
    elif u1 == "Paper":
        if u2 == "Rock":
            return(user1 + " wins")
        else:
            return(user2 + " wins")
    elif u1 == "Scissors":
        if u2 == "Paper":
            return(user1 + " wins")
        else:
            return(user2 + " wins")
    else:
        return("Invalid input! You have not entered rock, paper or scissors, try again.")
        sys.exit()

print(win(user1_answer, user2_answer))