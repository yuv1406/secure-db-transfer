import psycopg2
import csv
import hashlib
import os
from cryptography.fernet import Fernet

def extract_and_encrypt_postgres(host, port, user, password, database, table, output_csv_enc, hash_file, key_file):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # 1. Extract to CSV
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]
        
        temp_csv = "temp_post_extract.csv"
        with open(temp_csv, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(column_names)
            writer.writerows(rows)
        
        # 2. Calculate Hash
        sha256_hash = hashlib.sha256()
        with open(temp_csv, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        hash_val = sha256_hash.hexdigest()
        with open(hash_file, "w") as f:
            f.write(hash_val)
            
        # 3. Encrypt CSV (Optional but requested)
        key = Fernet.generate_key()
        with open(key_file, "wb") as kf:
            kf.write(key)
            
        cipher_suite = Fernet(key)
        with open(temp_csv, "rb") as f:
            file_data = f.read()
            
        encrypted_data = cipher_suite.encrypt(file_data)
        
        with open(output_csv_enc, "wb") as f:
            f.write(encrypted_data)
            
        # Cleanup
        os.remove(temp_csv)
        
        print(f"Extraction and encryption from Postgres successful.")
        print(f"Hash: {hash_val}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error extracting and encrypting from Postgres: {e}")
        return False

if __name__ == "__main__":
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    user = os.getenv("POSTGRES_USER", "user")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    database = os.getenv("POSTGRES_DB", "target_db")
    
    extract_and_encrypt_postgres(
        host, port, user, password, database, 
        "users", 
        "post_transfer.csv.enc", 
        "post_transfer.hash",
        "post_session.key"
    )
