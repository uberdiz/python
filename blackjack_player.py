import random
from time import sleep
def deal(cards, count):
    # Check if deck is empty and reshuffle if necessary
    if len(cards) < 35:
        #print("Deck is low on cards, reshuffling...")
        cards.extend(["2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD", "AD",
                      "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC", "AC",
                      "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH", "AH",
                      "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS", "AS"] * 6)
        random.shuffle(cards)
        count = 0

    p_hand = [cards.pop(0), cards.pop(0)]
    d_hand = [cards.pop(0), cards.pop(0)]

    # Update count based on dealt cards
    for card in p_hand + d_hand:
        count = update_count(card, count)

    return p_hand, d_hand, count
def update_count(card, count):
    # Update the count based on the card value
    if card[0] in ["A", "K", "Q", "J"] or card[:2] == "10":
        count -= 1
    elif card[0] in ["7", "8", "9"]:
        pass
    else:
        count += 1
    return count
def d_sum(hand):
    total = 0
    aces = 0
    for card in hand:
        if card[0] == "A":
            total += 11
            aces += 1
        elif card[0] in ["K", "Q", "J"] or card[:2] == "10":
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
    soft = False
    for card in hand:
        if card[0] == "A":
            if total + 11 <= 21:
                total += 11
                alt_total += 1
            else:
                total += 1
            soft = True
        elif card[0] in ["K", "Q", "J"] or card[:2] == "10":
            total += 10
            alt_total += 10
        else:
            total += int(card[0])
            alt_total += int(card[0])
    return (total, alt_total) if soft else (total,)
def hit(hand, cards, count):
    hand.append(cards.pop(0))
    card = hand[-1]
    count = update_count(card, count)
    return hand, count
def choose_action(d_card, p_total, soft=False):
    p_total = int(p_total[0])
    # Convert face cards to numerical values for dealer's card
    if d_card in ["J", "Q", "K", "10"]:
        d_card = 10
    elif d_card == "A":
        d_card = 11
    d_card = int(d_card)
    # Apply basic strategy rules with card counting in mind
    # Adjust for soft hands (when holding an Ace)
    if soft:
        if p_total >= 19:  # Soft 19 or 20 always stands
            return "stand"
        elif 18 <= p_total and d_card < 9:
            return "stand"
        else:
            return "hit" if d_card > 8 else "double"
    else:
        # Hard hands
        if p_total <= 8:
            return "hit"
        elif p_total == 9:
            return "double" if 3 <= d_card <= 6 else "hit"
        elif p_total == 10:
            return "double" if d_card <= 9 else "hit"
        elif p_total == 11:
            return "double"
        elif p_total == 12:
            return "stand" if 4 <= d_card <= 6 else "hit"
        elif 13 <= p_total <= 16:
            return "stand" if 2 <= d_card <= 6 else "hit"
        else:
            return "stand"
def stand(pluh, bet, d_pluh, d_hand, cards, count):
    global bank
    d_bust = False
    while d_pluh < 17:
        d_hand, count = hit(d_hand, cards, count)
        d_pluh = d_sum(d_hand)
        #print(f"Dealer's Hand: {d_pluh}")
        if d_pluh == 21:
            #print("Dealer's Hand: Blackjack")
            bank -= bet
            return True, count, d_pluh
        elif d_pluh > 21:
            #print("Dealer's Hand: Bust")
            bank += bet
            d_bust = True
    return d_bust, count, d_pluh  # Return d_pluh here
def double(hand, bet, cards, count):
    hand.append(cards.pop(0))
    bet *= 2
    card = hand[-1]
    count = update_count(card, count)
    return hand, bet, count
def split(hand, cards, count):
    hand1 = [hand[0], cards.pop(0)]
    hand2 = [hand[1], cards.pop(0)]
    count = update_count(hand1[1], count)
    count = update_count(hand2[1], count)
    return hand1, hand2, count
def display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False):
    return
def place_bet(bank, count):
    base_bet = 10 
    max_bet = 0.2 * bank 
    if count >= 5:
        bet = min(base_bet * (count - 3), max_bet)
    elif count >= 3:
        bet = min(base_bet * (count - 1), max_bet)
    elif count >= 1:
        bet = min(base_bet * (count), max_bet)
    else:
        bet = base_bet 
    bet = min(bet, bank)
    return bet
def plays(p_hand, soft, pluh, bet, d_hand, bank, count):
    #print(f"You have {bank} dollars. What is your bet? ")
    bet = place_bet(bank, count)
    done = False
    pluh = list(sum(p_hand))
    display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False)
    p_bust = False
    d_bust = False
    d_pluh = d_sum(d_hand)  # Initialize dealer's hand total early
    
    while not done:
        #print("What do you want to do? Hit, Stand, Double, or Split?")
        play = choose_action(d_hand[0][0], pluh)  # Call function to decide action
        #print(play)
            
        if play == "split" and p_hand[0][0] == p_hand[1][0]:
            hand1, hand2, count = split(p_hand, cards, count)
            # Split handling continues here...
            done = True
        elif play == "hit":
            p_hand, count = hit(p_hand, cards, count)
            pluh = list(sum(p_hand))
            display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False)
            if max(pluh) > 21:
                #print("Bust! Game over.")
                done = True
                p_bust = True
        elif play == "double" and bet * 2 <= bank:
            p_hand, bet, count = double(p_hand, bet, cards, count)
            pluh = list(sum(p_hand))
            display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=False)
            if max(pluh) > 21:
                #print("Bust! Game over.")
                done = True
                p_bust = True
            done = True
        elif play == "stand":
            d_bust, count, d_pluh = stand(pluh, bet, d_pluh, d_hand, cards, count)
            display(p_hand, soft, pluh, bet, d_hand, reveal_dealer=True)
            done = True
        elif play == "double" and bet * 2 > bank:
            print("You don't have enough money to double your bet.")
        else:
            print("Invalid action. Please choose Hit, Stand, Double, or Split.")
    
    # Finalize game outcome
    if p_bust:
        bank -= bet
    elif d_bust:
        bank += bet
    else:
        if pluh[0] > d_pluh:
            bank += bet
        elif pluh[0] < d_pluh:
            bank -= bet

    return bank, count
# Initialize deck and game variables
cards = ["2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD", "AD",
         "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC", "AC",
         "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH", "AH",
         "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS", "AS"]
cards *= 6
random.shuffle(cards)

card_count = 0
bank = 1000
gambling = True
counting = 0
while gambling:
    p_hand, d_hand, card_count = deal(cards, card_count)
    soft = False
    pluh = sum(p_hand)
    bet = 0
    bank, card_count = plays(p_hand, soft, pluh, bet, d_hand, bank, card_count)
    if bank <= 0:
        #print("You have no more money! Game over.")
        gambling = False
        break
    #print(f"Keep playing {card_count}? (yes or no): ")
    counting += 1
    if counting % 100000 == 0:
        print(f"{counting:,}")
    if counting != 1000000:
        yuh = "yes"
    else:
        yuh = "no"
        gambling = False
        bank = f"{bank:,}"
        print(f"Your final balance is {bank} dollars.")
