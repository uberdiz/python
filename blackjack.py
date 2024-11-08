import random


cards = ["2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD", "AD", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC", "AC", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH", "AH", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS", "AS"]
cards = cards * 6
random.shuffle(cards)



bank = 100
p_hand = []
d_hand = []
c1 = cards[0]
c2 = cards[1]
c3 = cards[2]
c4 = cards[3]

p_hand.append(c1)
p_hand.append(c3)
d_hand.append(c2)
d_hand.append(c4)
del cards[0]
del cards[0]
del cards[0]
del cards[0]

# If  sum + 11 <= 21 then it is a soft hand and user can choose what to do for the next hands, else it is a hard hand.
soft = False
split_hand = False
done = False
def d_sum(hand):
    sum = 0
    if hand[0][0] == "A" and sum + 11 <= 21:
            sum += 11
    elif hand[0][0] == "A" and sum + 11 > 21:
            sum += 1
    elif hand[0][0] == "K" or hand[0][0] == "Q" or hand[0][0] == "J":
            sum += 10
    else:
            sum += int(hand[0][0])
    return sum
def sum(hand):
    total = 0
    alt_total = 0
    global soft
    for card in hand:
        if card[0] == "A":
            if total + 11 <= 21:
                total += 11
                alt_total += 1
            else:
                total += 1
            soft = True
        elif card[0] in ["K", "Q", "J"]:
            total += 10
            alt_total += 10
        else:
            total += int(card[0])
            alt_total += int(card[0])
    return (total, alt_total) if soft else (total,)
def hit(hand):
    hand.append(cards[0])
    del cards[0]
    return hand
def stand(hand):
    # Dealers Turn
    hand.append(cards[0])
    del cards[0]
    return hand
def double(hand, bet):
    hand.append(cards[0])
    del cards[0]
    bet *= 2
    return hand, bet 
def split(hand):
    global split_hand
    split_hand = True
    # Split into two hands, each starting with one of the original cards
    hand1 = [hand[0], cards[0]]
    hand2 = [hand[1], cards[1]]
    del cards[0]
    del cards[0]
    return hand1, hand2

def display(p_hand, soft, pluh, bet, d_pluh):
    if soft == True:
        print(f"Bet: {bet} Player's Hand: {p_hand} Total: {pluh[0]} or {pluh[1]}")
        print(f"Dealer's Hand: {d_pluh}")
    else:
        print(f"Bet: {bet} Player's Hand: {p_hand} Total: {pluh[0]}")
        print("Dealer's Hand:", d_pluh)

bet = int(input(f"You have {bank} dollars. What is your bet? "))
while bet > bank:
    print("You don't have enough money")
    bet = int(input("What is your bet? "))

p_hand = ["AH", "AD"]
pluh = list(sum(p_hand))
d_pluh = int(d_sum(d_hand))
print(d_hand, p_hand)
display(p_hand, soft, pluh, bet, d_pluh)

while not done:
    play = input("What do you want to do? Hit, Stand, Double, or Split ? ").lower()
    
    # Handle "split" action
    if play == "split" and p_hand[0][0] == p_hand[1][0]:  # Check if split is possible
        hand1, hand2 = split(p_hand)
        # Display each hand separately
        print("\nYou chose to split!")
        print("First hand:")
        display(hand1, soft, list(sum(hand1)), bet, d_pluh)
        print("Second hand:")
        display(hand2, soft, list(sum(hand2)), bet, d_pluh)
        
        # Process each hand
        for i, hand in enumerate([hand1, hand2], start=1):
            done_hand = False
            while not done_hand:
                play = input(f"Hand {i}: Do you want to Hit or Stand? ").lower()
                if play == "hit":
                    hand = hit(hand)
                    pluh = list(sum(hand))
                    display(hand, soft, pluh, bet, d_pluh)
                    if max(pluh) > 21:  # Check for bust
                        print(f"Hand {i} is busted!")
                        done_hand = True
                elif play == "stand":
                    done_hand = True
                    print(f"Hand {i} stands.")
                    
        done = True  # End game after both hands are played

    # Handle other plays if not split
    elif play == "hit":
        p_hand = hit(p_hand)
        pluh = list(sum(p_hand))
        display(p_hand, soft, pluh, bet, d_pluh)
        if max(pluh) > 21:
            print("Bust! Game over.")
            done = True
    elif play == "double" and bet * 2 <= bank:
        p_hand, bet = double(p_hand, bet)
        pluh = list(sum(p_hand))
        display(p_hand, soft, pluh, bet, d_pluh)
        done = True
    elif play == "stand":
        done = True
        d_hand = stand(d_hand)
        pluh = list(sum(p_hand))
        display(p_hand, soft, pluh, bet, d_pluh)
    elif play == "double" and bet * 2 > bank:
        print("You don't have enough money to double your bet.")
    else:
        print("Invalid action. Please choose Hit, Stand, Double, or Split.")
