import random

cards = ["2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD", "AD",
         "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC", "AC",
         "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH", "AH",
         "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS", "AS"]
cards *= 6
random.shuffle(cards)

bank = 100
p_hand = []
d_hand = []
p_hand.extend([cards.pop(0), cards.pop(2)])
d_hand.extend([cards.pop(0), cards.pop(2)])

soft = False
split_hand = False
done = False
d_bust = False
p_bust = False
def d_sum(hand):
    total = 0
    aces = 0
    for card in hand:
        if card[0] == "A":
            total += 11
            aces += 1
        elif card[0] in ["K", "Q", "J"] or card[1] == "0":
            total += 10
        else:
            total += int(card[0])
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

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
        elif card[0] in ["K", "Q", "J"] or card[1] == "0":
            total += 10
            alt_total += 10
        else:
            total += int(card[0])
            alt_total += int(card[0])
    return (total, alt_total) if soft else (total,)

def hit(hand):
    hand.append(cards.pop(0))
    return hand

def stand(pluh, bet, d_pluh, d_hand):
    global bank, done
    while d_pluh < 17:
        hit(d_hand)
        d_pluh = d_sum(d_hand)
        print(f"Dealer's Hand: {d_pluh}")
        if d_pluh == 21:
            print("Dealer's Hand: Blackjack")
            bank -= bet
            done = True
            break
        elif d_pluh > 21:
            print("Dealer's Hand: Bust")
            bank += bet
            done = True
            break
    return done

def double(hand, bet):
    hand.append(cards.pop(0))
    bet *= 2
    return hand, bet 

def split(hand):
    global split_hand
    split_hand = True
    hand1 = [hand[0], cards.pop(0)]
    hand2 = [hand[1], cards.pop(0)]
    return hand1, hand2

def display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False):
    if soft:
        print(f"Bet: {bet} Player's Hand: {p_hand} Total: {pluh[0]} or {pluh[1]}")
    else:
        print(f"Bet: {bet} Player's Hand: {p_hand} Total: {pluh[0]}")
    if reveal_dealer:
        print(f"Dealer's Hand: {d_hand} Total: {d_sum(d_hand)}")
    else:
        print(f"Dealer's Hand: [{d_hand[0]}, ?]")

bet = int(input(f"You have {bank} dollars. What is your bet? "))
while bet > bank:
    print("You don't have enough money")
    bet = int(input("What is your bet? "))

pluh = list(sum(p_hand))
display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False)

while not done:
    play = input("What do you want to do? Hit, Stand, Double, or Split ? ").lower()
    if play == "split" and p_hand[0][0] == p_hand[1][0]:
        hand1, hand2 = split(p_hand)
        print("\nYou chose to split!")
        print("First hand:")
        display(hand1, soft, list(sum(hand1)), bet, d_hand, reveal_dealer=False)
        print("Second hand:")
        display(hand2, soft, list(sum(hand2)), bet, d_hand, reveal_dealer=False)
        for i, hand in enumerate([hand1, hand2], start=1):
            done_hand = False
            while not done_hand:
                play = input(f"Hand {i}: Do you want to Hit or Stand? ").lower()
                if play == "hit":
                    hand = hit(hand)
                    pluh = list(sum(hand))
                    display(hand, soft, pluh, bet, d_hand, reveal_dealer=False)
                    if max(pluh) > 21:
                        print(f"Hand {i} is busted!")
                        done_hand = True
                        p_bust = True
                elif play == "stand":
                    done_hand = True
                    print(f"Hand {i} stands.")
        done = True
    elif play == "hit":
        p_hand = hit(p_hand)
        pluh = list(sum(p_hand))
        display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False)
        if max(pluh) > 21:
            print("Bust! Game over.")
            done = True
            p_bust = True
    elif play == "double" and bet * 2 <= bank:
        p_hand, bet = double(p_hand, bet)
        pluh = list(sum(p_hand))
        display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False)
        if max(pluh) > 21:
            print("Bust! Game over.")
            done = True
            p_bust = True
        done = True
    elif play == "stand":
        done = stand(pluh, bet, d_sum(d_hand), d_hand)
        display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=True)
    elif play == "double" and bet * 2 > bank:
        print("You don't have enough money to double your bet.")
    else:
        print("Invalid action. Please choose Hit, Stand, Double, or Split.")
if d_bust == True:
    print("Dealer busts! You win!")
    bank += bet
elif p_bust == True:
    print("You bust! Dealer wins!")
    bank -= bet
else:
    if pluh > d_pluh:
        print("You win!")
        bank += bet
    elif pluh < d_pluh:
        print("Dealer wins!")
        bank -= bet
    else:
        print("It's a tie!")
# Reset all variables
