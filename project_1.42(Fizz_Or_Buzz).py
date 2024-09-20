#Write a Python program that prints the numbers from 1 to 100.
numbers = []
Fizz = 0
Buzz = 0
FizzBuzz = 0
fizzBuzz = {Fizz: 0, Buzz: 0, FizzBuzz: 0}
for i in range(1,101):
    numbers.append(i)
for x in numbers:
    if x % 3 == 0 and x % 5 == 0:
        y = "FizzBuzz"
        print("FizzBuzz")
        fizzBuzz.update({"FizzBuzz": fizzBuzz[FizzBuzz] + 1})
    elif x % 3 == 0:
        print("Fizz")
        fizzBuzz.update({"Fizz": fizzBuzz[Fizz] + 1})
    elif x % 5 == 0:
        print("Buzz")
        fizzBuzz.update({"Buzz": fizzBuzz[Buzz] + 1})
    else:
        print(x)
print(f"Fizz: {fizzBuzz[Fizz]}, Buzz: {fizzBuzz[Buzz]}, FizzBuzz: {fizzBuzz[FizzBuzz]}")
#But for multiples of 3, print "Fizz", 
# for multiples of 5, print "Buzz", 
# and for multiples of both 3 and 5, print "FizzBuzz".
