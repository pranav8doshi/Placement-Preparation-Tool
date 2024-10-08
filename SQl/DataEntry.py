import sqlite3

# Function to insert data into the test.db
def insert_sample_data():
    connection = sqlite3.connect('test.db')
    cursor = connection.cursor()

    # Insert sample data
    sample_data = [
        ('Alice', 30, 'HR'),
        ('Bob', 25, 'Engineering'),
        ('Charlie', 35, 'Sales'),
        ('Diana', 28, 'Marketing')
    ]

    cursor.executemany('''
        INSERT INTO employees (name, age, department)
        VALUES (?, ?, ?)
    ''', sample_data)

    connection.commit()
    connection.close()
    print("Sample data inserted successfully!")

# Call the function to insert data
insert_sample_data()
