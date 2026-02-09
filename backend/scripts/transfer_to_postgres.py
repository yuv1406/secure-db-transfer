from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import psycopg2
import struct
import io
import os
import base64

def ecc_decrypt_and_load(private_key_path, bundle_path, host, port, user, password, database, table):
    try:
        # 1. Load Receiver's Private Key (ECC)
        with open(private_key_path, "rb") as key_file:
            receiver_private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
            
        with open(bundle_path, "rb") as f:
            # Read Ephemeral Public Key
            eph_pub_len = struct.unpack("I", f.read(4))[0]
            eph_pub_bytes = f.read(eph_pub_len)
            
            # Read Encrypted Session Key
            enc_session_key_len = struct.unpack("I", f.read(4))[0]
            enc_session_key = f.read(enc_session_key_len)
            
            # Read Payload
            encrypted_payload = f.read()
            
        # 2. Deserialized Ephemeral Public Key
        ephemeral_public_key = serialization.load_pem_public_key(eph_pub_bytes)
        
        # 3. Perform ECDH to derive same shared secret
        shared_secret = receiver_private_key.exchange(ec.ECDH(), ephemeral_public_key)
        
        # 4. Derive same encryption key
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'session key encryption',
        ).derive(shared_secret)
        
        # 5. Decrypt the session key
        f_derived = Fernet(base64.urlsafe_b64encode(derived_key))
        session_key = f_derived.decrypt(enc_session_key)
        
        # 6. Decrypt payload with original session key
        cipher_suite = Fernet(session_key)
        decrypted_csv_data = cipher_suite.decrypt(encrypted_payload)
        
        # 7. Load into Postgres
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                created_at TIMESTAMP
            )
        """)
        
        cursor.execute(f"TRUNCATE TABLE {table}")
        
        f_io = io.StringIO(decrypted_csv_data.decode('utf-8'))
        next(f_io) # Skip header
        cursor.copy_from(f_io, table, sep=',', columns=('id', 'name', 'email', 'created_at'))
        
        conn.commit()
        print(f"ECC Decryption and transfer to Postgres successful.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error during ECC transfer to Postgres: {e}")
        return False

if __name__ == "__main__":
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    user = os.getenv("POSTGRES_USER", "user")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    database = os.getenv("POSTGRES_DB", "target_db")
    
    ecc_decrypt_and_load(
        "private_key.pem",
        "encrypted_payload.bundle",
        host, port, user, password, database,
        "users"
    )
