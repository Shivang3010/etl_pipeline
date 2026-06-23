import os
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any

# =====================================================================
# DATA QUALITY MATRIX DEFINITION
# =====================================================================
DQ_MATRIX = {
    "DQ-01": {"name": "PK_Uniqueness", "severity": "CRITICAL", "desc": "Company code or entity identifier must be unique."},
    "DQ-02": {"name": "Composite_Key_Uniqueness", "severity": "CRITICAL", "desc": "The combination of company_id and year must be unique per record."},
    "DQ-03": {"name": "FK_Integrity", "severity": "CRITICAL", "desc": "Referenced master data codes (e.g., country, industry) must exist."},
    "DQ-04": {"name": "Balance_Sheet_Equation", "severity": "WARNING", "desc": "Assets must match Liabilities + Equity within a 1% rounding threshold."},
    "DQ-05": {"name": "OPM_Cross_Check", "severity": "WARNING", "desc": "Calculated Operating Profit Margin must match the reported margin attribute."},
    "DQ-06": {"name": "Positive_Sales", "severity": "WARNING", "desc": "Gross Revenue/Sales must be non-negative."},
    "DQ-07": {"name": "Positive_Cash", "severity": "WARNING", "desc": "Ending cash balances should generally be non-negative."},
    "DQ-08": {"name": "Depreciation_CapEx_Ratio", "severity": "WARNING", "desc": "Depreciation cannot exceed total tangible asset values."},
    "DQ-09": {"name": "Tax_Rate_Sanity", "severity": "WARNING", "desc": "Effective tax rate should not realistically exceed 100% or be heavily negative."},
    "DQ-10": {"name": "Gross_Margin_Ceiling", "severity": "WARNING", "desc": "Gross profit margin cannot exceed 100%."},
    "DQ-11": {"name": "Interest_Coverage_Matching", "severity": "WARNING", "desc": "If interest expense is zero, Interest Coverage Ratio should be marked properly."},
    "DQ-12": {"name": "Dividend_Payout_Limit", "severity": "WARNING", "desc": "Dividends declared should not exceed total retained earnings for the period."},
    "DQ-13": {"name": "Inventory_Turnover_Sanity", "severity": "WARNING", "desc": "Negative inventory values are structurally impossible."},
    "DQ-14": {"name": "Current_Ratio_Limit", "severity": "WARNING", "desc": "Current assets or liabilities should be non-zero to avoid infinite ratio spikes."},
    "DQ-15": {"name": "Employee_Cost_Sanity", "severity": "WARNING", "desc": "Personnel expenses must be positive if employee headcount is greater than zero."},
    "DQ-16": {"name": "Audit_Status_Filled", "severity": "WARNING", "desc": "Financial statement validation flag should not be completely null or blank."}
}

class FinancialValidator:
    def __init__(self, df: pd.DataFrame, table_name: str = "financial_records"):
        self.df = df.copy()
        self.table_name = table_name
        self.validation_logs: List[Dict[str, Any]] = []
        
    def log_failure(self, rule_id: str, row_index: Any, context_val: Any):
        """Appends a systematic validation event to the internal logging array."""
        rule = DQ_MATRIX[rule_id]
        # Generate ISO format timestamp string
        current_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.validation_logs.append({
            "timestamp": current_ts,
            "table_name": self.table_name,
            "rule_id": rule_id,
            "severity": rule["severity"],
            "failure_reason": f"Failed {rule['name']} - {rule['desc']} (Offending Val: {context_val}, Row Index: {row_index})"
        })

    def write_logs_to_csv(self, output_dir: str = "output data"):
        """
        Safely flushes internal validation logging lists out to a persistent CSV audit log file.
        Appends records if the file already exists.
        """
        if not self.validation_logs:
            print("[INFO] No data quality violations found. Skipping file output logging.")
            return

        # Ensure the directory path exists safely
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "validation_failures.csv")
        
        headers = ["timestamp", "table_name", "rule_id", "severity", "failure_reason"]
        file_exists = os.path.exists(file_path)
        
        try:
            # Open file in 'a' (append) mode
            with open(file_path, mode="a", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                
                # Write header row ONLY if creating a brand new file
                if not file_exists:
                    writer.writeheader()
                    
                # Write all trapped audit failure rows
                for log in self.validation_logs:
                    # Filter dictionary to matching header columns explicitly
                    row_data = {k: log[k] for k in headers}
                    writer.writerow(row_data)
                    
            print(f"[SUCCESS] Appended {len(self.validation_logs)} audit rows to log tracking target: '{file_path}'")
        except Exception as e:
            print(f"[ERROR] Failed writing logs to CSV path: {e}")

    def execute_matrix(self) -> pd.DataFrame:
        """Runs the validation checks, logs errors, and drops Critical records."""
        critical_indices_to_drop = set()
        
        # --- DQ-01: Primary Key Uniqueness ---
        pks = self.df['company_id']
        duplicated_pks = self.df[pks.duplicated(keep=False)]
        for idx, row in duplicated_pks.iterrows():
            self.log_failure("DQ-01", idx, row['company_id'])
            critical_indices_to_drop.add(idx)

        # --- DQ-02: Composite Key Uniqueness ---
        composite_keys = self.df.duplicated(subset=['company_id', 'year'], keep=False)
        for idx, is_dup in composite_keys.items():
            if is_dup:
                self.log_failure("DQ-02", idx, f"{self.df.at[idx, 'company_id']}-{self.df.at[idx, 'year']}")
                critical_indices_to_drop.add(idx)

        # --- DQ-03: Foreign Key Integrity Simulation ---
        valid_countries = {'US', 'IN', 'UK'}
        for idx, row in self.df.iterrows():
            if row.get('country') not in valid_countries:
                self.log_failure("DQ-03", idx, row.get('country'))
                critical_indices_to_drop.add(idx)

        # --- Financial Vector Business Logics (DQ-04 to DQ-16) ---
        for idx, row in self.df.iterrows():
            # DQ-04: Balance Sheet Match Check
            total_assets = row.get('total_assets', 0)
            liabilities_equity = row.get('total_liabilities', 0) + row.get('total_equity', 0)
            if total_assets != 0 and abs(total_assets - liabilities_equity) / total_assets > 0.01:
                self.log_failure("DQ-04", idx, f"Variance: {abs(total_assets - liabilities_equity)}")

            # DQ-05: OPM Verification Engine
            revenue = row.get('revenue', 0)
            calculated_opm = (row.get('operating_income', 0) / revenue) if revenue != 0 else 0
            if abs(calculated_opm - row.get('opm', 0)) > 0.02:
                self.log_failure("DQ-05", idx, f"Calc: {calculated_opm:.2f}, Rep: {row.get('opm')}")

            # DQ-06: Non-Negative Sales Rule
            if row.get('revenue', 0) < 0:
                self.log_failure("DQ-06", idx, row['revenue'])

            # DQ-16: Missing Audit Check
            if pd.isna(row.get('audit_status')) or str(row.get('audit_status')).strip() == "":
                self.log_failure("DQ-16", idx, "NULL")

        # Drop invalid elements
        cleaned_df = self.df.drop(index=list(critical_indices_to_drop))
        
        # Write to validation_failures.csv automatically upon execution
        self.write_logs_to_csv()
        
        return cleaned_df

# =====================================================================
# PIPELINE DEMORUNNER
# =====================================================================
if __name__ == "__main__":
    print("--- Running Validator Output Pipeline Engine ---")
    
    mock_data = pd.DataFrame([
        # Row 0: Valid Row
        {"company_id": "C01", "year": 2023, "country": "IN", "total_assets": 100, "total_liabilities": 40, "total_equity": 60, "revenue": 200, "operating_income": 40, "opm": 0.20, "audit_status": "Audited"},
        # Row 1: CRITICAL - Duplicate Key Violation
        {"company_id": "C01", "year": 2023, "country": "IN", "total_assets": 100, "total_liabilities": 40, "total_equity": 60, "revenue": 200, "operating_income": 40, "opm": 0.20, "audit_status": "Audited"},
        # Row 2: WARNINGS - Out of boundaries numbers
        {"company_id": "C02", "year": 2023, "country": "US", "total_assets": 500, "total_liabilities": 100, "total_equity": 200, "revenue": -450, "operating_income": 10, "opm": 0.15, "audit_status": None}
    ])

    validator = FinancialValidator(mock_data, table_name="company_annual_financials")
    clean_df = validator.execute_matrix()