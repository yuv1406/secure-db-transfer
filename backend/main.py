from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json
import mysql.connector
import psycopg2
from datetime import datetime
from backend.scripts.generate_keys import generate_ecc_keys
from backend.scripts.load_dummy_data_mysql import load_dummy_data
from backend.scripts.extract_mysql_encrypt import extract_and_encrypt
from backend.scripts.encrypt_payload import ecc_encrypt_session_key
from backend.scripts.transfer_to_postgres import ecc_decrypt_and_load
from backend.scripts.extract_postgres_encrypt import extract_and_encrypt_postgres
from backend.scripts.compare_hash import compare_hashes
from backend.scripts.audit_logger import log_transfer
from backend.scripts.generate_pdf import generate_pdf

app = FastAPI(title="Secure DB Transfer API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DBConfig(BaseModel):
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_username: str = "user"
    mysql_password: str = "password"
    mysql_database: str = "source_db"
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_username: str = "user"
    postgres_password: str = "password"
    postgres_database: str = "target_db"

class QueryRequest(BaseModel):
    config: DBConfig
    target: str # "source" or "destination"
    query: str

transfer_status = {
    "status": "idle", # idle, running, completed, failed
    "current_step": "None",
    "logs": [],
    "result": None
}

def run_transfer_pipeline(config: DBConfig):
    global transfer_status
    transfer_status["status"] = "running"
    transfer_status["logs"] = []
    
    try:
        def log_step(step_name):
            transfer_status["current_step"] = step_name
            transfer_status["logs"].append(f"{datetime.now().isoformat()}: {step_name}")
            print(f"PIPELINE: {step_name}")

        # Step 0: Ensure ECC keys exist
        if not os.path.exists("private_key.pem"):
            log_step("Generating ECC keys")
            generate_ecc_keys("private_key.pem", "public_key.pem")

        # Step 1: Load Dummy Data (Optional, but included in flow)
        log_step("Loading dummy data into MySQL")
        if not load_dummy_data(config.mysql_host, config.mysql_port, config.mysql_username, config.mysql_password, config.mysql_database):
            raise Exception("Failed to load dummy data")

        # Step 2: Extract and Encrypt from MySQL
        log_step("Extracting and encrypting data from MySQL")
        if not extract_and_encrypt(config.mysql_host, config.mysql_port, config.mysql_username, config.mysql_password, config.mysql_database, "users", "pre_transfer.csv.enc", "pre_transfer.hash", "session.key"):
            raise Exception("Failed to extract and encrypt from MySQL")

        # Step 3: ECC Hybrid Encryption
        log_step("Performing ECC hybrid encryption on payload")
        if not ecc_encrypt_session_key("public_key.pem", "session.key", "pre_transfer.csv.enc", "encrypted_payload.bundle"):
            raise Exception("Failed ECC hybrid encryption")

        # Step 4: Transfer and Load into Postgres
        log_step("Decrypting (ECC) and loading data into Postgres")
        if not ecc_decrypt_and_load("private_key.pem", "encrypted_payload.bundle", config.postgres_host, config.postgres_port, config.postgres_username, config.postgres_password, config.postgres_database, "users"):
            raise Exception("Failed to transfer to Postgres")

        # Step 5: Extract from Postgres for Verification
        log_step("Extracting data from Postgres for integrity verification")
        if not extract_and_encrypt_postgres(config.postgres_host, config.postgres_port, config.postgres_username, config.postgres_password, config.postgres_database, "users", "post_transfer.csv.enc", "post_transfer.hash", "post_session.key"):
            raise Exception("Failed to extract from Postgres")

        # Step 6: Compare Hashes
        log_step("Comparing integrity hashes")
        hashes_match = compare_hashes("pre_transfer.hash", "post_transfer.hash")
        final_status = "PASS" if hashes_match else "FAIL"

        # Step 7: Audit Log
        log_step("Writing immutable audit log")
        with open("pre_transfer.hash", "r") as f: pre_h = f.read().strip()
        with open("post_transfer.hash", "r") as f: post_h = f.read().strip()
        
        audit_data = {
            "username": config.mysql_username,
            "source_database": config.mysql_database,
            "destination_database": config.postgres_database,
            "record_count": 20, # Updated to 20 rows as requested
            "hash_before": pre_h,
            "hash_after": post_h,
            "transfer_status": final_status
        }
        log_transfer("audit_log.json", audit_data)

        # Step 8: Generate PDF
        log_step("Generating PDF audit report")
        generate_pdf("audit_log.json", "secure_transfer_report.pdf")

        transfer_status["status"] = "completed"
        transfer_status["result"] = {
            "success": hashes_match,
            "hash_before": pre_h,
            "hash_after": post_h,
            "timestamp": datetime.now().isoformat()
        }
        log_step("Transfer Pipeline Completed Successfully")

    except Exception as e:
        transfer_status["status"] = "failed"
        transfer_status["logs"].append(f"ERROR: {str(e)}")
        log_step(f"Transfer Pipeline Failed: {str(e)}")

@app.post("/start-transfer")
async def start_transfer(config: DBConfig, background_tasks: BackgroundTasks):
    if transfer_status["status"] == "running":
        raise HTTPException(status_code=400, detail="Transfer already in progress")
    
    background_tasks.add_task(run_transfer_pipeline, config)
    return {"message": "Transfer started"}

@app.get("/progress")
async def get_progress():
    return transfer_status

@app.get("/result")
async def get_result():
    if transfer_status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Transfer not completed yet")
    return transfer_status["result"]

@app.get("/audit-logs")
async def get_audit_logs():
    if os.path.exists("audit_log.json"):
        with open("audit_log.json", "r") as f:
            return json.load(f)
    return []

@app.get("/download-report")
async def download_report():
    if os.path.exists("secure_transfer_report.pdf"):
        return FileResponse("secure_transfer_report.pdf", media_type="application/pdf", filename="secure_transfer_report.pdf")
    raise HTTPException(status_code=404, detail="Report not found")

@app.post("/test-connection")
async def test_connection(config: DBConfig):
    results = {"mysql": "failed", "postgres": "failed", "messages": []}
    
    # Test MySQL
    try:
        m_conn = mysql.connector.connect(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_username,
            password=config.mysql_password,
            database=config.mysql_database,
            connect_timeout=5
        )
        m_conn.close()
        results["mysql"] = "success"
    except Exception as e:
        results["messages"].append(f"MySQL Error: {str(e)}")

    # Test Postgres
    try:
        p_conn = psycopg2.connect(
            host=config.postgres_host,
            port=config.postgres_port,
            user=config.postgres_username,
            password=config.postgres_password,
            database=config.postgres_database,
            connect_timeout=5
        )
        p_conn.close()
        results["postgres"] = "success"
    except Exception as e:
        results["messages"].append(f"Postgres Error: {str(e)}")
    if results["mysql"] == "success" and results["postgres"] == "success":
        return {"status": "success", "message": "All connections verified successfully."}
    else:
        return {"status": "error", "message": " | ".join(results["messages"])}

@app.post("/execute-query")
async def execute_sql_query(request: QueryRequest):
    try:
        config = request.config
        if request.target == "source":
            # MySQL
            conn = mysql.connector.connect(
                host=config.mysql_host,
                port=config.mysql_port,
                user=config.mysql_username,
                password=config.mysql_password,
                database=config.mysql_database
            )
        else:
            # Postgres
            conn = psycopg2.connect(
                host=config.postgres_host,
                port=config.postgres_port,
                user=config.postgres_username,
                password=config.postgres_password,
                database=config.postgres_database
            )
        
        cursor = conn.cursor()
        cursor.execute(request.query)
        
        if cursor.description:
            columns = [i[0] for i in cursor.description]
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            # Convert datetime objects to string for JSON serialization
            for res in results:
                for k, v in res.items():
                    if isinstance(v, datetime):
                        res[k] = v.isoformat()
        else:
            conn.commit()
            results = {"message": "Query executed successfully."}
            
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
