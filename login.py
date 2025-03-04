import hashlib
import os

# In-memory storage (replace with a database for persistent storage)
users = {}

def hash_password(password):
    """Hashes a password using SHA-256."""
    salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return salt.hex(), hashed_password

def verify_password(stored_salt, stored_hash, password):
    """Verifies a password against a stored hash."""
    salt = bytes.fromhex(stored_salt)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return hashed_password == stored_hash

def register_user(username, password):
    """Registers a new user, storing credentials in memory."""
    global users  # Access the global 'users' dictionary

    if username in users:
        return "Username already exists."

    salt, hashed_password = hash_password(password)
    users[username] = {"salt": salt, "hash": hashed_password}

    return "User registered successfully."

def login_user(username, password):
    """Logs in a user, verifying credentials from memory."""
    global users # Access the global 'users' dictionary

    if username not in users:
        return "Invalid username or password."

    stored_salt = users[username]["salt"]
    stored_hash = users[username]["hash"]

    if verify_password(stored_salt, stored_hash, password):
        return "Login successful."
    else:
        return "Invalid username or password."

# Example usage:
if __name__ == "__main__":
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            username = input("Enter username: ")
            password = input("Enter password: ")
            print(register_user(username, password))
        elif choice == "2":
            username = input("Enter username: ")
            password = input("Enter password: ")
            print(login_user(username, password))
        elif choice == "3":
            break
        else:
            print("Invalid choice.")

