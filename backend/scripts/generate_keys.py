from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def generate_ecc_keys(private_key_path, public_key_path):
    # Generate SECP256R1 (NIST P-256) curve keys
    private_key = ec.generate_private_key(
        ec.SECP256R1(),
        backend=default_backend()
    )
    
    # Save private key
    with open(private_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Save public key
    public_key = private_key.public_key()
    with open(public_key_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    print(f"ECC keys (P-256) generated: {private_key_path}, {public_key_path}")

if __name__ == "__main__":
    generate_ecc_keys("private_key.pem", "public_key.pem")
