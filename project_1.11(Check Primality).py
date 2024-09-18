num = int(input("Please give me a number: "))
divisor_list = list(range(1, num+1))
divisors = []
for number in divisor_list:
    if num % number == 0:
        divisors.append(number)
if divisors[1] == num:
    print("Number is Prime.")
elif divisors[1] == num:
    print("Number is NOT Prime.")
print(divisors)