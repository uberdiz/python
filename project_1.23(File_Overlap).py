PN = []
HN = []
with open('PrimeNumbers.txt', 'r') as file:
    # Loop through each line in the file
    for line in file:
        # Print or process the line
        x = line.strip()  # .strip() removes extra whitespace
        PN.append(x)
with open('HappyNumbers.txt', 'r') as file:
    # Loop through each line in the file
    for line in file:
        # Print or process the line
        x = line.strip()  # .strip() removes extra whitespace
        HN.append(x)

overlap = [x for x in PN if x in HN]
print(overlap)