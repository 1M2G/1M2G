from datetime import datetime

now = datetime.now()
print(now)  # Shows full date and time
print(now.date())  # Only date part
print(now.time()) 

from datetime import datetime

my_birthday = datetime(1995, 8, 25)  # Year, Month, Day
print(my_birthday)

specific_time = datetime(2023, 10, 5, 15, 30, 45)


#strftime() — Convert datetime to string in a desired format.

now = datetime.now()
print(now.strftime("%Y-%m-%d"))  # Output: 2025-05-01
print(now.strftime("%d/%m/%Y"))  # Output: 01/05/2025

date_str = "01/05/2025"
date_obj = datetime.strptime(date_str, "%d/%m/%Y")
print(date_obj)

from datetime import timedelta

today = datetime.now()
tomorrow = today + timedelta(days=1)
yesterday = today - timedelta(days=1)

print("Tomorrow:", tomorrow)
print("Yesterday:", yesterday)

d1 = datetime(2025, 5, 10)
d2 = datetime(2025, 5, 1)
difference = d1 - d2
print(difference.days)  # Output: 9


#How to calculate someone’s age

dob = datetime(1998, 4, 15)
today = datetime.now()
age = today.year - dob.year

# Adjust if birthday hasn’t occurred yet this year

if (today.month, today.day) < (dob.month, dob.day):
    age -= 1

print("Age:", age)


#Useful formatting codes for dates

'''%Y – Full year (2025)

%y – Short year (25)

%m – Month (01-12)

%d – Day (01-31)

%H – Hour (00-23)

%M – Minute (00-59)

%S – Second (00-59)'''