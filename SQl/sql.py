from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
import os

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': '2211',  # Replace with your MySQL password
    'database': 'org'
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
        suggestion = suggest_correction(query)
        return jsonify({"error": error_message, "suggestion": suggestion})
    finally:
        cursor.close()
        conn.close()
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

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
    # Placeholder for AI suggestion logic
    # You can use the Gemini API or implement your own logic here
    return f"Check your SQL syntax for the query: {query}"

if __name__ == '__main__':
    app.run(debug=True)
