import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.loader import orchestrate_strict_warehouse_load, initialize_production_database
from src.etl.normaliser import normalize_year, normalize_ticker

def apply_timeline_quality_filter(input_file_path: str, minimum_years: int = 5) -> str:
    """
    Inspects sheet rows before warehouse compilation, discarding entities 
    that possess fewer than the required years of financial data.
    """
    print(f"\n[AUDIT MATRIX] Running historical continuity filter (Min Threshold: {minimum_years} Years)...")
    excel_file = pd.ExcelFile(input_file_path)
    
    if "balance_sheets" not in excel_file.sheet_names:
        return input_file_path # Fallback directly to pass-through if testing simple data
        
    # Read sheets for pre-flight timeline parsing
    bs_df = pd.read_excel(input_file_path, sheet_name="balance_sheets")
    companies_df = pd.read_excel(input_file_path, sheet_name="companies")
    sectors_df = pd.read_excel(input_file_path, sheet_name="industry_sectors")
    
    # Run inline normalization to get true group metrics
    bs_df["clean_company_id"] = bs_df["company_id"].apply(normalize_ticker)
    bs_df["clean_year"] = bs_df["year"].apply(normalize_year)
    
    # Count unique operational tracking periods per company entity
    history_counts = bs_df.groupby("clean_company_id")["clean_year"].nunique()
    valid_tickers = history_counts[history_counts >= minimum_years].index.tolist()
    
    dropped_tickers = history_counts[history_counts < minimum_years].index.tolist()
    if dropped_tickers:
        print(f"[TIMELINE WARNING] Dropped fragmented profiles (fewer than {minimum_years} years history): {dropped_tickers}")
    
    # Re-compile clean datasets matched against strict criteria
    clean_bs = bs_df[bs_df["clean_company_id"].isin(valid_tickers)].drop(columns=["clean_company_id", "clean_year"])
    clean_companies = companies_df[companies_df["company_id"].apply(normalize_ticker).isin(valid_tickers)]
    
    # Write back clean partitioned matrices over temporary workbook path space
    patched_workbook_path = "notebooks/filtered_production_data.xlsx"
    with pd.ExcelWriter(patched_workbook_path, engine="openpyxl") as writer:
        sectors_df.to_excel(writer, sheet_name="industry_sectors", index=False)
        clean_companies.to_excel(writer, sheet_name="companies", index=False)
        clean_bs.to_excel(writer, sheet_name="balance_sheets", index=False)
        
    return patched_workbook_path


if __name__ == "__main__":
    db_path = "db/production_warehouse.db"
    schema_path = "db/schema.sql"
    raw_workbook_path = "notebooks/sample_data.xlsx"
    
    os.makedirs("notebooks", exist_ok=True)
    os.makedirs("db", exist_ok=True)

    # 1. Clear out historical stale database traces
    if os.path.exists(db_path):
        try: os.remove(db_path)
        except PermissionError: pass

    # 2. Build continuous multi-year history tracking blocks for testing
    print("[PRE-FLIGHT] Compiling mock financial sheets with structural timeline variations...")
    with pd.ExcelWriter(raw_workbook_path, engine="openpyxl") as writer:
        pd.DataFrame([{"sector_id": 1, "sector_name": "Technology Services", "industry_group": "IT", "macro_economic_sector": "Tech"}]).to_excel(writer, sheet_name="industry_sectors", index=False)
        
        pd.DataFrame([
            {"company_id": "INFY", "company_name": "Infosys Ltd", "isin_code": "INE009A01021", "sector_id": 1, "incorporation_country": "IN"},
            {"company_id": "TCS", "company_name": "Tata Consultancy Services", "isin_code": "INE467B01029", "sector_id": 1, "incorporation_country": "IN"},
            {"company_id": "SHORT_HIST", "company_name": "Fragile Inc", "isin_code": "INE111A11111", "sector_id": 1, "incorporation_country": "IN"}
        ]).to_excel(writer, sheet_name="companies", index=False)
        
        # INFY = 5 clean years (Passes), TCS = 5 complex parsed years (Passes), SHORT_HIST = 2 years (Gets Dropped)
        pd.DataFrame([
            {"company_id": "INFY", "year": "2020", "cash_and_equivalents": 10},
            {"company_id": "INFY", "year": "2021", "cash_and_equivalents": 12},
            {"company_id": "INFY", "year": "2022", "cash_and_equivalents": 14},
            {"company_id": "INFY", "year": "2023", "cash_and_equivalents": 16},
            {"company_id": "INFY", "year": "2024", "cash_and_equivalents": 18},
            
            {"company_id": "TCS.NS", "year": "CY 2020", "cash_and_equivalents": 30},
            {"company_id": "TCS.NS", "year": "2021-03-31", "cash_and_equivalents": 32},
            {"company_id": "TCS.NS", "year": "Collected in 2022 on-site", "cash_and_equivalents": 34},
            {"company_id": "TCS.NS", "year": "1995-12-25T14:23:11Z", "cash_and_equivalents": 36}, # Historical year parsed safely now!
            {"company_id": "TCS.NS", "year": "2101", "cash_and_equivalents": 38}, # Deep forecast upper-bound parsed safely now!
            
            {"company_id": "SHORT_HIST", "year": "2023", "cash_and_equivalents": 1},
            {"company_id": "SHORT_HIST", "year": "2024", "cash_and_equivalents": 2},
        ]).to_excel(writer, sheet_name="balance_sheets", index=False)

    # 3. Clean out fragmented company streams using the timeline filter matrix
    sanitized_workbook = apply_timeline_quality_filter(raw_workbook_path, minimum_years=5)

    # 4. Stream processed records safely to production storage
    orchestrate_strict_warehouse_load(
        input_file_path=sanitized_workbook,
        db_path=db_path,
        schema_sql_path=schema_path
    )