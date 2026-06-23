import sqlite3
import os

def execute_exploratory_suite(db_path, sql_file_path):
    if not os.path.exists(db_path):
        print(f"[ERROR] Database warehouse not found at: {db_path}")
        return
    if not os.path.exists(sql_file_path):
        print(f"[ERROR] SQL file not found at: {sql_file_path}")
        return

    print(f"🔗 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"📖 Reading exploratory queries from: {sql_file_path}\n")
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    # Split individual queries by the standard semi-colon separator
    # This prevents SQLite from executing empty blocks or comment lines
    queries = sql_content.split(';')

    query_idx = 1
    for query in queries:
        cleaned_query = query.strip()
        
        # Skip empty lines or pure comment blocks
        if not cleaned_query or cleaned_query.startswith('--') and len(cleaned_query.split('\n')) == 1:
            continue
            
        print(f"==================================================================")
        print(f"▶️ EXECUTING QUERY {query_idx}")
        print(f"==================================================================")
        
        # Extract and print just the descriptive header comment if it exists
        lines = cleaned_query.split('\n')
        headers = [line.strip() for line in lines if line.strip().startswith('--')]
        if headers:
            print("\n".join(headers))

        try:
            cursor.execute(cleaned_query)
            
            # Fetch table column headers
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                print(f"\n📋 Schema Layout: { ' | '.join(columns) }")
                print("-" * 66)
                
                rows = cursor.fetchall()
                if not rows:
                    print("   (Query returned 0 rows matching your current mock records)")
                for row in rows:
                    print(f"   { ' | '.join(str(val) for val in row) }")
            else:
                print("   Command completed successfully (No rows returned).")
                
            print("\n")
            query_idx += 1
            
        except sqlite3.Error as sql_err:
            # Catch failures elegantly without halting the entire test pipeline sweep
            print(f"⚠️ Query Execution Interrupted: {sql_err}\n")

    conn.close()
    print("🏁 Analytical usability suite verification complete.")

if __name__ == "__main__":
    execute_exploratory_suite(
        db_path="db/production_warehouse.db",
        sql_file_path="notebooks/exploratory_queries.sql"
    )