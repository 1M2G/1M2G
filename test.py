import mysql.connector  #use pip install mysql-connector-python

def create_database(mydb, db_name):
    try:
        mycursor = mydb.cursor()
        mycursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully.")
    except mysql.connector.Error as err:
        if err.errno == 1007:  # Database already exists
            print(f"Database '{db_name}' already exists.")
        else:
            print(f"Error creating database: {err}")

def show_databases(mydb):
    mycursor = mydb.cursor()
    mycursor.execute("SHOW DATABASES")
    for x in mycursor:
        print(x)

def use_database(mydb, db_name):
    try:
        mydb.database = db_name  # Switch to the specified database
        print(f"Using database '{db_name}'.")
    except mysql.connector.Error as err:
        print(f"Error using database: {err}")

def create_table(mydb, table_name):
    try:
        mycursor = mydb.cursor()
        # Example table creation (customize as needed)
        query = f"""
        CREATE TABLE {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255) UNIQUE
        )
        """
        mycursor.execute(query)
        print(f"Table '{table_name}' created successfully.")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")

def describe_table(mydb, table_name):
    try:
        mycursor = mydb.cursor()
        mycursor.execute(f"DESCRIBE {table_name}")
        result = mycursor.fetchall()
        for x in result:
            print(x)
    except mysql.connector.Error as err:
        print(f"Error describing table: {err}")

def main():
    mydb = mysql.connector.connect(
        host="your_host",  # Replace with your MySQL host
        user="your_user",  # Replace with your MySQL username
        password="your_password"  # Replace with your MySQL password
    )

    while True:
        print("\nDatabase Operations Menu:")
        print("1. Create Database")
        print("2. Show Databases")
        print("3. Use Database")
        print("4. Create Table")
        print("5. Describe Table")
        print("6. Exit")

        choice = input("Enter your choice: ")

        try:
            choice = int(choice)  # Convert input to integer
            if choice == 1:
                db_name = input("Enter database name: ")
                create_database(mydb, db_name)
            elif choice == 2:
                show_databases(mydb)
            elif choice == 3:
                db_name = input("Enter database name to use: ")
                use_database(mydb, db_name)
            elif choice == 4:
                db_name = mydb.database  # Get the currently used database
                if db_name:  # Make sure a database is selected
                    table_name = input("Enter table name: ")
                    create_table(mydb, table_name)
                else:
                    print("Please select a database first (option 3).")
            elif choice == 5:
                db_name = mydb.database
                if db_name:
                    table_name = input("Enter table name to describe: ")
                    describe_table(mydb, table_name)
                else:
                    print("Please select a database first (option 3).")
            elif choice == 6:
                break
            else:
                print("Invalid choice. Please try again.")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except mysql.connector.Error as err:
            print(f"MySQL Error: {err}")  # Handle MySQL errors

    mydb.close()  # Close the database connection

if __name__ == "__main__":
    main()
