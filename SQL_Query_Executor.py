from flask import Flask, request, jsonify,render_template
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

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

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
        # Capture the error message
        error_message = str(err)

        # Use the suggest_correction function to simplify the error message
        suggestion = suggest_correction(error_message)
        
        # Return the error and suggestion in the response
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

def suggest_correction(error_message):
    # Prompt to simplify the error message
    prompt = f"Give precise answer in 10 words max.The following is a database error: {error_message}. Your task is to act as a tutor and explain the error to the user instead of solving the error, give tips. Sql is not case sensative so ignore  capitalization"

    try:
        # Start a chat session with the model
        chat_session = model.start_chat(history=[{
            "role": "user",
            "parts": [{"text": prompt}]
        }])

        # Send the error message to the model
        response = chat_session.send_message(prompt)
        
        # Extract the suggestion from the response
        suggestion = response.text.split("**Output:**")[1].split("**")[0] if "**Output:**" in response.text else response.text
        
    except Exception as e:
        suggestion = f"Could not generate a suggestion: {str(e)}"
    
    return suggestion



@app.route('/')
def home():
      return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

