import random
rand = random.randint(0, 100)
element = int(rand)
max = int(100)
L1 = []
L2 = []
for e in range(random.randint(0, max)):
    L1.append(e)
for f in range(random.randint(0, max)):
    L2.append(f)

overlap = []
for d in L1:
    if d in L2:
        overlap.append(d)
print(L1)
print(L2)
print(overlap)
