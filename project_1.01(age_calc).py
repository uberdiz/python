import datetime
now = datetime.datetime.now()
name = input('Give me your name: ').capitalize()
year = int(input('Give me the year you were born: '))
month = int(input('Give me the month you were born: '))
day = int(input('Give me the day you were born: '))
year100 = year + 100
time = datetime.datetime(year100, month, day)
birth = time - now
birth_year = birth.days // 365
birth_day = birth.days % 365
print(f"{name} will turn 100 in {birth_year} years and {birth_day} days")
