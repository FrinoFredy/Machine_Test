import mysql.connector
import csv
import re
from datetime import datetime

# Establishing a connection to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="040828",
    database="hotel_db"
)

cursor = db.cursor()

# Create RoomCategory table
cursor.execute("""
CREATE TABLE IF NOT EXISTS RoomCategory (
    CAT_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL
)
""")

# Create Rooms table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Rooms (
    Room_ID INT AUTO_INCREMENT PRIMARY KEY,
    Room_Number VARCHAR(10) NOT NULL,
    CAT_ID INT,
    Price_Per_Day DECIMAL(10, 2),
    Rate_Type ENUM('Daily', 'Hourly') NOT NULL DEFAULT 'Daily',
    FOREIGN KEY (CAT_ID) REFERENCES RoomCategory(CAT_ID)
)
""")

# Create Customers table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Customers (
    Customer_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(100),
    Last_Name VARCHAR(100),
    Email VARCHAR(100),
    Phone VARCHAR(15),
    Address TEXT
)
""")

# Create Booking table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Bookings (
    ID INT AUTO_INCREMENT PRIMARY KEY,  -- Auto-incrementing ID
    Booking_ID VARCHAR(7),               -- Final Booking ID
    Customer_ID INT,
    Room_ID INT,
    Date_of_Booking DATE,
    Date_of_Occupancy DATE,
    No_of_Days INT,
    Advance_Received DECIMAL(10, 2),
    Total_Amount DECIMAL(10, 2),
    Tax DECIMAL(10, 2) DEFAULT 0,
    Housekeeping_Charges DECIMAL(10, 2) DEFAULT 0,
    Misc_Charges DECIMAL(10, 2) DEFAULT 0,
    Booking_Type ENUM('Daily', 'Hourly') NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
    FOREIGN KEY (Room_ID) REFERENCES Rooms(Room_ID)
)
""")


# Function to generate the Booking ID
def generate_booking_id(auto_increment_id):
    prefix = "BK"  # Example prefix
    return f"{prefix}{str(auto_increment_id).zfill(5)}"  # Pads the number with leading zeros


# Function for Booking
def pre_booking():
    customer_id = input("Enter Customer ID: ")
    room_id = input("Enter Room ID: ")
    date_of_booking = datetime.today().date()
    date_of_occupancy = input("Enter Date of Occupancy (YYYY-MM-DD): ")
    num_of_days = int(input("Enter Number of Days of Occupancy: "))
    advance_received = float(input("Enter Advance Received: "))

    # Validate date of occupancy
    try:
        date_of_occupancy = datetime.strptime(date_of_occupancy, "%Y-%m-%d").date()
        if date_of_occupancy < date_of_booking:
            print("Date of occupancy cannot be earlier than today's date.")
            return
    except ValueError:
        print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
        return

    # Fetch room rate and type
    cursor.execute("SELECT Price_Per_Day, Rate_Type FROM Rooms WHERE Room_ID = %s", (room_id,))
    room_data = cursor.fetchone()
    if room_data is None:
        print("Invalid Room ID.")
        return

    price_per_day, rate_type = room_data
    price_per_day = float(price_per_day)

    # Calculate total amount and charges
    if rate_type == 'Hourly':
        total_amount = price_per_day * num_of_days
    else:
        total_amount = price_per_day * num_of_days

    tax = total_amount * 0.25
    housekeeping_charges = 50
    misc_charges = 30

    total_amount += tax + housekeeping_charges + misc_charges

    # Generate booking ID
    auto_increment_id = cursor.execute("SELECT IFNULL(MAX(ID), 0) + 1 FROM Bookings")
    auto_increment_id = cursor.fetchone()[0]
    booking_id = generate_booking_id(auto_increment_id)

    query = """
    INSERT INTO Bookings (Booking_ID, Customer_ID, Room_ID, Date_of_Booking, Date_of_Occupancy, No_of_Days, 
    Advance_Received, Total_Amount, Tax, Housekeeping_Charges, Misc_Charges, Booking_Type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(query, (booking_id, customer_id, room_id, date_of_booking, date_of_occupancy, num_of_days,
                               advance_received, total_amount, tax, housekeeping_charges, misc_charges, rate_type))
        db.commit()
        print(f"Booking created successfully with Booking ID: {booking_id}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Function to display rooms category wise
def display_category_wise():
    query = """
        SELECT RoomCategory.Name, Rooms.Room_Number, Rooms.Price_Per_Day
        FROM Rooms
        JOIN RoomCategory ON Rooms.CAT_ID = RoomCategory.CAT_ID
        ORDER BY RoomCategory.Name
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            print(f"Category: {row[0]}, Room Number: {row[1]}, Rate per Day: ${row[2]:.2f}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Function to display rooms occupied for the next two days
def list_occupied_rooms():
    query = """
        SELECT Rooms.Room_Number, RoomCategory.Name, Bookings.Date_of_Occupancy
        FROM Bookings
        JOIN Rooms ON Bookings.Room_ID = Rooms.Room_ID
        JOIN RoomCategory ON Rooms.CAT_ID = RoomCategory.CAT_ID
        WHERE Bookings.Date_of_Occupancy BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 2 DAY)
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            for row in results:
                print(f"Room Number: {row[0]}, Category: {row[1]}, Occupied on: {row[2]}")
        else:
            print("No rooms are occupied for the next two days.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Function to list room by rates
def list_rooms_by_rate():
    query = """
        SELECT RoomCategory.Name, Rooms.Room_Number, Rooms.Price_Per_Day
        FROM Rooms
        JOIN RoomCategory ON Rooms.CAT_ID = RoomCategory.CAT_ID
        ORDER BY Rooms.Price_Per_Day ASC
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            print(f"Category: {row[0]}, Room Number: {row[1]}, Rate per Day: ${row[2]:.2f}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Function to search room by booking id
def search_by_id():
    booking_id = input("Enter Booking ID : ")
    query = """
        SELECT Bookings.Booking_ID, Customers.First_Name, Customers.Last_Name, Customers.Email, Customers.Phone, 
        Rooms.Room_Number
        FROM Bookings
        JOIN Customers ON Bookings.Customer_ID = Customers.Customer_ID
        JOIN Rooms ON Bookings.Room_ID = Rooms.Room_ID
        WHERE Bookings.Booking_ID = %s
    """
    try:
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        if result:
            print(f"Booking ID: {result[0]}, Customer: {result[1]} {result[2]}, Email: {result[3]}, "
                  f"Phone: {result[4]}, Room Number: {result[5]}")
        else:
            print("Booking ID not found.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Function to display rooms which are not booked
def display_unbooked_rooms():
    query = """
        SELECT Rooms.Room_Number, RoomCategory.Name, Rooms.Price_Per_Day
        FROM Rooms
        LEFT JOIN Bookings ON Rooms.Room_ID = Bookings.Room_ID
        JOIN RoomCategory ON Rooms.CAT_ID = RoomCategory.CAT_ID
        WHERE Bookings.Room_ID IS NULL
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            for row in results:
                print(f"Room Number: {row[0]}, Category: {row[1]}, Rate per Day: ${row[2]:.2f}")
        else:
            print("All rooms are currently booked.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Function to update room status
def update_room_status():
    booking_id = input("Enter Booking ID : ")
    query = "DELETE FROM Bookings WHERE Booking_ID = %s"
    try:
        cursor.execute(query, (booking_id,))
        db.commit()
        print("Room status updated to unoccupied.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Function to store all records and display it
def store_records_in_file():
    query = """
        SELECT Bookings.Booking_ID, Customers.First_Name, Customers.Last_Name, Rooms.Room_Number, 
        Bookings.Date_of_Booking, Bookings.Date_of_Occupancy
        FROM Bookings
        JOIN Customers ON Bookings.Customer_ID = Customers.Customer_ID
        JOIN Rooms ON Bookings.Room_ID = Rooms.Room_ID
    """
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        with open('bookings.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Booking ID', 'First Name', 'Last Name', 'Room Number', 'Date of Booking',
                             'Date of Occupancy'])
            writer.writerows(records)
        print("Records stored in bookings.csv")
    except mysql.connector.Error as err:
        print(f"Error: {err}")


def display_records_from_file():
    try:
        with open('bookings.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                print(', '.join(row))
    except FileNotFoundError:
        print("File not found.")


# Function to add a customer
def add_customer():
    while True:
        first_name = input("Enter first name : ")
        if re.fullmatch("[A-Za-z]{2,25}", first_name):
            break
        else:
            print("INVALID! Enter only alphabets of length 2 to 25")

    while True:
        last_name = input("Enter last name : ")
        if re.fullmatch("[A-Za-z]{2,25}", last_name):
            break
        else:
            print("INVALID! Enter only alphabets of length 2 to 25")

    while True:
        email = input("Enter the email id : ")
        if re.fullmatch(r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$', email):
            break
        else:
            print("INVALID !! Enter a valid email id")

    while True:
        phone = input("Enter the phone number : ")
        if re.fullmatch(r'^[6-9]\d{9}$', phone):
            break
        else:
            print("INVALID !! Enter a valid phone number")
    while True:
        address = input("Enter the address : ")
        if address:
            break
        else:
            print("Address cannot be empty!")

    query = """
    INSERT INTO Customers (First_Name, Last_Name, Email, Phone, Address)
    VALUES (%s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(query, (first_name, last_name, email, phone, address))
        db.commit()
        print("Customer added successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    while True:
        print("""
                                          ------------------------------------------------
                                                WELCOME TO HOTEL ROOM BOOKING SYSTEM
                                          ------------------------------------------------
                      -> Choose an option:
                      1. Display Rooms Category Wise
                      2. List Rooms Occupied For Next Two Days
                      3. List of Rooms in their Increasing Order of Rate per Day
                      4. Search Rooms By Booking ID
                      5. Display Unbooked Rooms
                      6. Update Room Status
                      7. Store Records In File
                      8. Display Records From File
                      9. Add Customer
                      10. Book Room
                      11. Exit Program
                """)
        choice = input("Enter your choice : ")
        if choice == "1":
            display_category_wise()
        elif choice == "2":
            list_occupied_rooms()
        elif choice == "3":
            list_rooms_by_rate()
        elif choice == "4":
            search_by_id()
        elif choice == "5":
            display_unbooked_rooms()
        elif choice == "6":
            update_room_status()
        elif choice == "7":
            store_records_in_file()
        elif choice == "8":
            display_records_from_file()
        elif choice == "9":
            add_customer()
        elif choice == "10":
            pre_booking()
        elif choice == "11":
            print("Exiting Program...")
            break
        else:
            print("Invalid Choice !!!")


if __name__ == "__main__":
    main()
