import os

def compare_hashes(pre_hash_file, post_hash_file):
    try:
        if not os.path.exists(pre_hash_file) or not os.path.exists(post_hash_file):
            print("One or both hash files missing.")
            return False
            
        with open(pre_hash_file, "r") as f:
            pre_hash = f.read().strip()
        with open(post_hash_file, "r") as f:
            post_hash = f.read().strip()
            
        if pre_hash == post_hash:
            print(f"PASS: Hashes match. ({pre_hash})")
            return True
        else:
            print(f"FAIL: Hashes do not match!")
            print(f"Pre-transfer:  {pre_hash}")
            print(f"Post-transfer: {post_hash}")
            return False
    except Exception as e:
        print(f"Error comparing hashes: {e}")
        return False

if __name__ == "__main__":
    compare_hashes("pre_transfer.hash", "post_transfer.hash")
