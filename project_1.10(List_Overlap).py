import random
a = random.sample(range(1,30), 12)
b = random.sample(range(1,30), 16)
overlap = [x for x in a if x in b]
overlap.sort()
print(overlap)