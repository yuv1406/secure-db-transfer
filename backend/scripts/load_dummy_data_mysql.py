import mysql.connector
import sys
import os

def load_dummy_data(host, port, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sample data generation
        users = [(f'User {i}', f'user{i}@example.com') for i in range(1, 21)]

        # Clear existing data for fresh start
        cursor.execute("TRUNCATE TABLE users")

        cursor.executemany("INSERT INTO users (name, email) VALUES (%s, %s)", users)
        conn.commit()
        print(f"Successfully loaded {len(users)} records into MySQL.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error loading dummy data: {e}")
        return False

if __name__ == "__main__":
    # Get parameters from env or defaults
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", 3306))
    user = os.getenv("MYSQL_USER", "user")
    password = os.getenv("MYSQL_PASSWORD", "password")
    database = os.getenv("MYSQL_DATABASE", "source_db")
    
    load_dummy_data(host, port, user, password, database)
