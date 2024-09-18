num = int(input('Give me a number '))
check = int(input('Is divisible by '))
equ = (num%2)
four = (num%4)
check1 = (num%check)
if equ == 0:
    print("number is even")
if equ != 0:
    print("number is odd")
if four == 0:
    print("number is multiple of 4")
if check1 == 0:
    check = str(check)
    print("number is multiple of " + check)
