# Secure Hybrid Inter-DB Transfer MVP

A secure, auditable data transfer pipeline between MySQL and PostgreSQL featuring ECC hybrid encryption, integrity verification, and an immutable audit trail.

## 🚀 Key Features
- **ECC Hybrid Encryption**: Uses ECIES (P-256) to securely transfer session keys.
- **Integrity Verification**: SHA-256 hash comparison ensures data consistency.
- **Immutable Logs**: Hash-chained audit logs stored in JSON format.
- **PDF Reporting**: Generates a tamper-evident audit report for every transfer.
- **SQL Console**: Live UI for querying source and destination databases.
- **Generalized Config**: Support for any DB host/port (Source vs. Destination).

---

## 🛠️ Setup Instructions

### 1. Prerequisites
- **Docker** and **Docker Compose**
- **Python 3.9+**
- **Node.js 18+**

### 2. Infrastructure Setup
Start the MySQL and PostgreSQL databases:
```bash
docker-compose up -d
```

### 3. Backend Setup
Initialize the Python environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

Run the FastAPI server:
```bash
./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup
Install React dependencies and start the dev server:
```bash
cd frontend
npm install
npm run dev
```

---

## 📖 How to Use

1. **Access the Dashboard**: Open [http://localhost:5173](http://localhost:5173).
2. **Configure Databases**:
   - The default configuration points to the Docker containers (localhost:3306 for MySQL, localhost:5432 for Postgres).
   - Use the **Test Connection** button to verify connectivity.
3. **Execute Transfer**:
   - Click **Start Transfer**.
   - Watch the live logs:
     - 20 records are loaded into MySQL.
     - Data is extracted, encrypted using ECC, and transferred to Postgres.
     - Integrity is verified by comparing pre/post hashes.
4. **Download Audit Report**: Once finished, click **Download PDF Audit Report**.
5. **Inspect Data**: Use the **🔍 SQL Query Console** tab to run queries like `SELECT * FROM users;` against either database.

---

## 🔒 Security Workflow
1. **Key Generation**: Unique ECC (P-256) keys are generated for each session.
2. **Hybrid Encryption**: AES-256 symmetric encryption for data, RSA/ECC for the session key.
3. **Immutability**: Every audit log entry contains a `current_hash` that includes the `previous_hash`, creating a cryptographic chain.
