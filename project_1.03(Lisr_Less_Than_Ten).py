a = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
for x in a:
   if x< 10: print([x])
print("____________Challenge____________")
print( [ x for x in a if x<10 ] )