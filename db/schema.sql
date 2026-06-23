-- ============================================================================
-- LAYER 1: CORE CORPORATE LAYER
-- ============================================================================ 

CREATE TABLE IF NOT EXISTS industry_sectors (
    sector_id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite auto-increment syntax
    sector_name VARCHAR(100) NOT NULL UNIQUE,
    industry_group VARCHAR(100) NOT NULL,
    macro_economic_sector VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS companies (
    company_id VARCHAR(20) PRIMARY KEY, -- Clean standard tickers like TCS, INFY, AAPL
    company_name VARCHAR(255) NOT NULL,
    isin_code VARCHAR(12) UNIQUE NOT NULL, -- International Securities Identification Number
    sector_id INT NOT NULL,
    incorporation_country CHAR(2) NOT NULL DEFAULT 'IN', -- ISO 2-letter country codes
    is_actively_traded BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Kept standard for SQLite compatibility
    
    CONSTRAINT fk_companies_sector FOREIGN KEY (sector_id) 
        REFERENCES industry_sectors(sector_id) ON DELETE RESTRICT
);

-- ============================================================================
-- LAYER 2: FINANCIAL REPORTING STATEMENTS (Normalized Rows)
-- ============================================================================

CREATE TABLE IF NOT EXISTS balance_sheets (
    balance_sheet_id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite compatible identity primary key
    company_id VARCHAR(20) NOT NULL,
    fiscal_year INT NOT NULL,
    reporting_period VARCHAR(10) NOT NULL DEFAULT 'FY', -- FY, Q1, Q2, H1
    filing_date DATE,
    
    -- Assets Mapping
    cash_and_equivalents NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    inventories NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    current_assets NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    property_plant_equipment NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    total_assets NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    
    -- Liabilities & Equity Mapping
    current_liabilities NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    total_liabilities NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    retained_earnings NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    total_equity NUMERIC(18, 4) NOT NULL DEFAULT 0.0000,
    
    CONSTRAINT fk_bs_company FOREIGN KEY (company_id) 
        REFERENCES companies(company_id) ON DELETE CASCADE,
    CONSTRAINT uq_bs_composite UNIQUE (company_id, fiscal_year, reporting_period)
);