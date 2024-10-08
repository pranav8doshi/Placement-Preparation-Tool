from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
import os
import google.generativeai as genai  # Import Google Gemini API for suggestions

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': '2211',  # Replace with your MySQL password
    'database': 'org'
}

# Configure Google Gemini API
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC-u1iHOoklku1mvfOZtW9Umr0UWF8tkDU")
genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Connect to the database
def create_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/execute_query', methods=['POST'])
def execute_query():
    query = request.json.get('query')
    
    # Connect to the database
    conn = create_db_connection()
    cursor = conn.cursor()

    # Try to execute the query
    try:
        cursor.execute(query)
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            return jsonify(results)
        else:
            conn.commit()
            return jsonify({"message": "Query executed successfully."})
    except mysql.connector.Error as err:
        # Handle error
        error_message = str(err)
        suggestion = suggest_correction(error_message)
        return jsonify({"error": error_message, "suggestion": suggestion})
    finally:
        cursor.close()
        conn.close()

@app.route('/show_tables', methods=['GET'])
def show_tables():
    # Connect to the database
    conn = create_db_connection()
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()

    table_info = []
    for (table_name,) in tables:
        cursor.execute(f"DESCRIBE {table_name};")
        columns = cursor.fetchall()
        columns_info = [{"name": col[0], "type": col[1], "null": col[2], "key": col[3], "default": col[4], "extra": col[5]} for col in columns]
        table_info.append({"table_name": table_name, "columns": columns_info})

    return jsonify(table_info)

def suggest_correction(query):
    
    prompt = f"The following is the  error: {query}. Tell in brief what is the error."
    try:
        response = genai.generate_text(
            model="models/gemini-1.5-flash",  # Specify the correct Gemini model
            prompt=prompt,
            temperature=generation_config["temperature"],
            max_output_tokens=generation_config["max_output_tokens"],
            top_p=generation_config["top_p"],
            top_k=generation_config["top_k"]
        )
        suggestion = response.generations[0].text if response.generations else "No suggestions available."
    except Exception as e:
        suggestion = f"Could not generate a suggestion: {str(e)}"
    
    return suggestion

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
