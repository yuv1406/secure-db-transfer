from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import os
import struct
import base64

def ecc_encrypt_session_key(public_key_path, session_key_path, encrypted_csv_path, output_bundle_path):
    try:
        # 1. Load Receiver's Public Key
        with open(public_key_path, "rb") as key_file:
            receiver_public_key = serialization.load_pem_public_key(key_file.read())
            
        # 2. Load Session Key (the one used for AES/Fernet)
        with open(session_key_path, "rb") as f:
            session_key = f.read()

        # 3. Generate Ephemeral ECC Key Pair
        ephemeral_private_key = ec.generate_private_key(ec.SECP256R1())
        ephemeral_public_key = ephemeral_private_key.public_key()
        
        # 4. Perform ECDH to derive shared secret
        shared_secret = ephemeral_private_key.exchange(ec.ECDH(), receiver_public_key)
        
        # 5. Derive encryption key for the session key using HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'session key encryption',
        ).derive(shared_secret)
        
        # 6. Encrypt the session key with the derived key (using Fernet for simplicity)
        f_derived = Fernet(base64.urlsafe_b64encode(derived_key))
        encrypted_session_key = f_derived.encrypt(session_key)
        
        # 7. Serialize Ephemeral Public Key
        ephemeral_pub_bytes = ephemeral_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # 8. Load encrypted payload (AES/Fernet encrypted CSV)
        with open(encrypted_csv_path, "rb") as f:
            encrypted_payload = f.read()
            
        # 9. Create bundle: 
        # [4 bytes eph_pub_len][eph_pub][4 bytes enc_session_key_len][enc_session_key][payload]
        with open(output_bundle_path, "wb") as f:
            f.write(struct.pack("I", len(ephemeral_pub_bytes)))
            f.write(ephemeral_pub_bytes)
            f.write(struct.pack("I", len(encrypted_session_key)))
            f.write(encrypted_session_key)
            f.write(encrypted_payload)
            
        print(f"ECC Hybrid encryption successful. Bundle created: {output_bundle_path}")
        return True
    except Exception as e:
        print(f"Error during ECC hybrid encryption: {e}")
        return False

if __name__ == "__main__":
    ecc_encrypt_session_key(
        "public_key.pem",
        "session.key",
        "pre_transfer.csv.enc",
        "encrypted_payload.bundle"
    )
