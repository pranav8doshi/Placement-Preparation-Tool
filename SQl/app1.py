import os
import sqlite3
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai  # Use Google Gemini AI

# Initialize Flask app
app = Flask(__name__)

# Configure Google Gemini API
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC-u1iHOoklku1mvfOZtW9Umr0UWF8tkDU")
genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Initialize database (SQLite)
def init_db():
    connection = sqlite3.connect('test.db')
    cursor = connection.cursor()
    # Create a sample table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            department TEXT
        )
    ''')
    connection.commit()
    connection.close()

# Insert sample data into the database
def insert_sample_data():
    connection = sqlite3.connect('test.db')
    cursor = connection.cursor()

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

# Call functions to initialize and insert sample data
init_db()
insert_sample_data()

# Validate and execute SQL query
def validate_sql_query(user_query):
    try:
        connection = sqlite3.connect('test.db')
        cursor = connection.cursor()
        cursor.execute(user_query)
        connection.commit()
        result = cursor.fetchall()
        connection.close()
        return True, result
    except sqlite3.Error as e:
        return False, str(e)

# Use Gemini AI to correct SQL query
def correct_sql_query(user_query):
    prompt = f"The following SQL query is incorrect: {user_query}. Please correct it."
    try:
        response = genai.generate_text(
            model="models/gemini-1.5-flash",  # Specify the correct Gemini model
            prompt=prompt,
            temperature=generation_config["temperature"],
            max_output_tokens=generation_config["max_output_tokens"],
            top_p=generation_config["top_p"],
            top_k=generation_config["top_k"]
        )
        return response.candidates[0]['output'].strip()
    except Exception as e:
        return str(e)

# Route for the HTML page
@app.route('/')
def home():
    return render_template('index.html')

# Chatbot route to check the SQL query
@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.json.get('query')

    # Check if the query is valid
    is_valid, response = validate_sql_query(user_input)
    
    if is_valid:
        return jsonify({"status": "success", "result": response})
    else:
        # If invalid, correct the SQL query using Gemini AI
        corrected_query = correct_sql_query(user_input)
        return jsonify({"status": "error", "error": response, "corrected_query": corrected_query})

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
