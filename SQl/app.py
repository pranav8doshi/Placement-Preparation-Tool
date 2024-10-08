import os
import sqlite3
from flask import Flask, request, jsonify, render_template
import openai
from openai import OpenAIError  # Updated import

# Initialize Flask app
app = Flask(__name__)

# Configure Google Generative AI API (Gemini)
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC-u1iHOoklku1mvfOZtW9Umr0UWF8tkDU")
openai.api_key = API_KEY

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

init_db()

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
        response = openai.Completion.create(
            model="gemini-1.5-flash",
            prompt=prompt,
            temperature=generation_config["temperature"],
            max_tokens=generation_config["max_output_tokens"],
            top_p=generation_config["top_p"],
            top_k=generation_config["top_k"]
        )
        return response.choices[0].text.strip()
    except OpenAIError as e:
        return str(e)
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