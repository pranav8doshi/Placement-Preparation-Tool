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

# Initialize the SQLite database
def init_db():
    connection = sqlite3.connect('test.db')
    cursor = connection.cursor()
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

# Function to get the database schema (table names and columns)
def get_database_schema():
    connection = sqlite3.connect('test.db')
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema[table_name] = [col[1] for col in columns]
    connection.close()
    return schema

# Validate and execute SQL query
def execute_sql_query(user_query, schema):
    try:
        connection = sqlite3.connect('test.db')
        cursor = connection.cursor()
        cursor.execute(user_query)
        connection.commit()
        
        if user_query.strip().lower().startswith("select"):
            result = cursor.fetchall()  # Fetch result for SELECT queries
        else:
            result = "Query executed successfully"
        
        connection.close()
        return True, result
    except sqlite3.Error as e:
        error_message = str(e)
        # Suggest corrections for invalid table/column names
        corrected_query = suggest_corrections(user_query, error_message, schema)
        return False, corrected_query

# Suggest table/column corrections based on the schema
def suggest_corrections(user_query, error_message, schema):
    if "no such table" in error_message:
        return suggest_table_correction(user_query, schema)
    elif "no such column" in error_message:
        return suggest_column_correction(user_query, schema)
    else:
        return f"Error: {error_message}"

# Suggest table corrections
def suggest_table_correction(user_query, schema):
    available_tables = list(schema.keys())
    prompt = f"The SQL query contains an invalid table name. Your query: {user_query}. Available tables: {available_tables}. Suggest a corrected query."
    try:
        response = genai.generate_text(
            model="models/gemini-1.5-flash",
            prompt=prompt,
            temperature=generation_config["temperature"],
            max_output_tokens=generation_config["max_output_tokens"],
            top_p=generation_config["top_p"],
            top_k=generation_config["top_k"]
        )
        return response.candidates[0]['output'].strip()
    except Exception as e:
        return f"Error: {str(e)}. Available tables: {available_tables}."

# Suggest column corrections
def suggest_column_correction(user_query, schema):
    words = user_query.split()
    table_name = ""
    for word in words:
        if word in schema:
            table_name = word
            break

    if table_name:
        available_columns = schema[table_name]
        prompt = f"The SQL query contains an invalid column name in the table '{table_name}'. Your query: {user_query}. Available columns: {available_columns}. Suggest a corrected query."
        try:
            response = genai.generate_text(
                model="gemini-1.5-flash",
                prompt=prompt,
                temperature=generation_config["temperature"],
                max_output_tokens=generation_config["max_output_tokens"],
                top_p=generation_config["top_p"],
                top_k=generation_config["top_k"]
            )
            return response.candidates[0]['output'].strip()
        except Exception as e:
            return f"Error: {str(e)}. Available columns in '{table_name}': {available_columns}."
    else:
        return f"Error: Could not identify the table in the query. Available tables: {list(schema.keys())}."

# Route to render HTML page
@app.route('/')
def home():
    return render_template('index.html')

# Route for chatbot to handle SQL queries
@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_query = request.json.get('query')

    # Get database schema
    schema = get_database_schema()

    # Execute query and validate
    is_valid, response = execute_sql_query(user_query, schema)
    
    if is_valid:
        return jsonify({"status": "success", "result": response})
    else:
        return jsonify({"status": "error", "error": response})

# Run Flask app
if __name__ == '__main__':
    init_db()  # Initialize the database on startup
    app.run(debug=True)
