num = int(input("Please give me a number: "))
divisor_list = list(range(1, num+1))
divisors = []
for number in divisor_list:
    if num % number == 0:
        divisors.append(number)
print(divisors)