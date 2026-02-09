from fpdf import FPDF
import json
import os

class AuditReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Secure DB Transfer Audit Report', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(audit_log_path, output_pdf_path):
    try:
        if not os.path.exists(audit_log_path):
            print("Audit log not found. Cannot generate PDF.")
            return False
            
        with open(audit_log_path, "r") as f:
            logs = json.load(f)
            
        if not logs:
            print("Audit log is empty.")
            return False
            
        # Get the latest entry
        entry = logs[-1]
        data = entry["data"]
        
        pdf = AuditReport()
        pdf.add_page()
        pdf.set_font('Arial', '', 12)
        
        pdf.cell(0, 10, f"Timestamp: {entry['timestamp']}", ln=True)
        pdf.cell(0, 10, f"Entry Hash: {entry['current_hash']}", ln=True)
        pdf.cell(0, 10, f"Previous Hash: {entry['previous_hash']}", ln=True)
        pdf.ln(10)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Transfer Details:", ln=True)
        pdf.set_font('Arial', '', 12)
        
        for key, value in data.items():
            pdf.cell(0, 10, f"{key.replace('_', ' ').capitalize()}: {value}", ln=True)
            
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Final Status: " + str(data.get("transfer_status", "UNKNOWN")), ln=True)
        
        pdf.output(output_pdf_path)
        print(f"PDF report generated: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

if __name__ == "__main__":
    generate_pdf("audit_log.json", "secure_transfer_report.pdf")
