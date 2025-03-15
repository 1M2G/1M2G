import random
import time

def guessing_game():
    """A simple guessing game using a while loop."""

    secret_number = random.randint(1, 100)
    guess = None
    attempts = 0

    print("Welcome to the Guessing Game!")
    print("I'm thinking of a number between 1 and 100.")

    while guess != secret_number:
        try:
            guess = int(input("Enter your guess: "))
            attempts += 1

            if guess < secret_number:
                print("Too low! Try again.")
            elif guess > secret_number:
                print("Too high! Try again.")
            else:
                print(f"Congratulations! You guessed the number in {attempts} attempts.")

        except ValueError:
            print("Invalid input. Please enter a number.")

def countdown_timer():
    """A simple countdown timer using a while loop."""

    try:
        seconds = int(input("Enter the number of seconds to countdown: "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    while seconds > 0:
        print(f"Time remaining: {seconds} seconds")
        time.sleep(1)  # Pause for 1 second
        seconds -= 1

    print("Time's up!")

def simple_calculator():
    """A simple calculator using a while loop."""

    print("Simple Calculator")
    print("Enter 'q' to quit.")

    while True:
        try:
            num1 = float(input("Enter the first number: "))
            operator = input("Enter an operator (+, -, *, /): ")
            num2 = float(input("Enter the second number: "))

            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                if num2 == 0:
                    print("Cannot divide by zero.")
                    continue
                result = num1 / num2
            else:
                print("Invalid operator.")
                continue

            print(f"Result: {result}")

        except ValueError:
            user_input = input("Invalid input. Enter 'q' to quit, or press enter to continue: ").lower()
            if user_input == 'q':
                break
            else:
              continue
        except ZeroDivisionError:
            print("Cannot divide by zero")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

def main():
    while True:
        print("\nChoose a project:")
        print("1. Guessing Game")
        print("2. Countdown Timer")
        print("3. Simple Calculator")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            guessing_game()
        elif choice == '2':
            countdown_timer()
        elif choice == '3':
            simple_calculator()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

