import getpass

def register(users):
    username = input("Enter new username: ")
    if username in users:
        print("Username already exists. Try a different one.")
        return
    password = getpass.getpass("Enter new password: ")
    users[username] = password
    print("Registration successful!")

def login(users):
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    if users.get(username) == password:
        print("Login successful!")
    else:
        print("Invalid username or password.")

def main():
    users = {}  # Store user credentials
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ")
        if choice == '1':
            register(users)
        elif choice == '2':
            login(users)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()


