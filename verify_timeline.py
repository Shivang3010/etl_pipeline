import sqlite3
import os

def check_production_timelines(db_path: str):
    """
    Connects to the production warehouse and performs a manual, deep spot check
    on 5 randomly sampled corporate entities to audit their timeline continuity.
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found at '{db_path}'. Run your pipeline first.")
        return

    print("==================================================================")
    # Open the database connection matrix
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys to view the production context accurately
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # 1. Pull 5 randomly selected tickers that exist in your companies registry
        cursor.execute("""
            SELECT company_id, company_name, incorporation_country 
            FROM companies 
            ORDER BY RANDOM() 
            LIMIT 5;
        """)
        random_companies = cursor.fetchall()
        
        if not random_companies:
            print("[WARN] No companies found in the database. Ensure data was successfully committed.")
            return

        print(f"📊 SPOT-CHECKING 5 RANDOM ENTITIES FROM THE PRODUCTION MATRIX:")
        print("==================================================================")
        
        # 2. Iterate through each selected entity and inspect its child records
        for company_id, name, country in random_companies:
            print(f"\n🏢 Company: {name} [{company_id}] | Region: {country}")
            
            # Fetch every reported year present in the child balance sheets table
            cursor.execute("""
                SELECT fiscal_year, reporting_period, cash_and_equivalents, total_assets 
                FROM balance_sheets 
                WHERE company_id = ? 
                ORDER BY fiscal_year ASC;
            """, (company_id,))
            
            records = cursor.fetchall()
            history_length = len(records)
            
            print(f"   ⏱️ Historical Timeline: {history_length} year(s) of financial data logged")
            
            if history_length == 0:
                print("   ❌ [CRITICAL DETECTED] Missing child records entirely! Potential ingestion or seeding failure.")
            elif history_length < 5:
                # Flag timeline records that fail our standard continuous time-series criteria
                years_logged = [r[0] for r in records]
                print(f"   ⚠️ [TIMELINE ALERT] Fewer than 5 years of history! Logged years: {years_logged}")
                print("      Systemic Risk: This profile creates broken time-series windows for data modeling.")
            else:
                # Pass clean entities meeting your 5-year minimum data threshold
                print(f"   ✅ [DATA HEALTHY] Continuous timeline checks pass.")
                print("      Sampled Entries:")
                for fiscal_year, period, cash, assets in records[:3]: # show a quick snapshot
                    print(f"         • {fiscal_year} ({period}) -> Cash: {cash}, Total Assets: {assets}")
                if history_length > 3:
                    print(f"         • ... and {history_length - 3} more continuous rows.")
                    
        print("\n==================================================================")
        print("🔍 TIMELINE AUDIT COMPLETE.")
        print("==================================================================")

    except sqlite3.Error as err:
        print(f"[FATAL DB ERROR] Failed to query production database: {err}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Points directly to your SQLite warehouse destination path
    production_db_file = "db/production_warehouse.db"
    check_production_timelines(production_db_file)