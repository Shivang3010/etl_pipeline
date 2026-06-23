-- ====================================================================
-- ENTERPRISE DATA WAREHOUSE USABILITY SUITE
-- Target: Verification of 7 Core & 5 Supplementary Tables
-- ====================================================================

-- QUERY 1: CORE MARKET RATIOS - Price-to-Earnings (P/E) Continuous Baselines
-- Purpose: Validates cross-table convergence between child market prices and child income metrics.
SELECT 
    c.company_id,
    c.company_name,
    i.fiscal_year,
    m.closing_price,
    (i.net_income / NULLIF(c.total_outstanding_shares, 0)) AS earnings_per_share,
    m.closing_price / NULLIF((i.net_income / NULLIF(c.total_outstanding_shares, 0)), 0) AS price_to_earnings_ratio
FROM companies c
JOIN income_statements i ON c.company_id = i.company_id
JOIN market_prices m ON c.company_id = m.company_id AND i.fiscal_year = m.fiscal_year
WHERE m.reporting_period = 'FY'
ORDER BY price_to_earnings_ratio DESC;


-- QUERY 2: PROFITABILITY BENCHMARKING - Top Performers by Operating Profit Margin (OPM)
-- Purpose: Tests precision math on high-scale text variables converted to floating decimals.
SELECT 
    c.company_id,
    c.company_name,
    s.sector_name,
    i.fiscal_year,
    i.operating_income,
    i.total_revenue,
    (i.operating_income / NULLIF(i.total_revenue, 0)) * 100 AS operating_profit_margin_pct
FROM companies c
JOIN industry_sectors s ON c.sector_id = s.sector_id
JOIN income_statements i ON c.company_id = i.company_id
WHERE i.total_revenue > 0
ORDER BY operating_profit_margin_pct DESC
LIMIT 10;


-- QUERY 3: TIMELINE GAP ANALYSIS - Identification of Missing Operational Periods
-- Purpose: Audits your 5-year timeline requirement to surface companies with missing time-series entries.
SELECT 
    company_id,
    COUNT(DISTINCT fiscal_year) AS total_logged_periods,
    MIN(fiscal_year) AS earliest_year,
    MAX(fiscal_year) AS latest_year,
    (MAX(fiscal_year) - MIN(fiscal_year) + 1) - COUNT(DISTINCT fiscal_year) AS missing_years_count
FROM balance_sheets
GROUP BY company_id
HAVING missing_years_count > 0 OR total_logged_periods < 5
ORDER BY total_logged_periods ASC;


-- QUERY 4: RISK MITIGATION ANALYSIS - DuPont Identity Decomposition (ROE Breakdown)
-- Purpose: Combines complex multi-table parameters (P&L and BS) to verify financial integrity.
SELECT 
    c.company_id,
    b.fiscal_year,
    (i.net_income / NULLIF(i.total_revenue, 0)) AS net_profit_margin,
    (i.total_revenue / NULLIF(b.total_assets, 0)) AS asset_turnover,
    (b.total_assets / NULLIF(b.total_equity, 0)) AS equity_multiplier,
    (i.net_income / NULLIF(b.total_equity, 0)) * 100 AS return_on_equity_pct
FROM companies c
JOIN income_statements i ON c.company_id = i.company_id
JOIN balance_sheets b ON c.company_id = b.company_id AND i.fiscal_year = b.fiscal_year
WHERE i.reporting_period = 'FY' AND b.total_equity > 0;


-- QUERY 5: SOLVENCY TRACKING - Liquidity Runway Profiles (Current Ratio Trends)
-- Purpose: Checks numerical type safety bounds against zero division elements.
SELECT 
    company_id,
    fiscal_year,
    current_assets,
    current_liabilities,
    current_assets - current_liabilities AS net_working_capital,
    CASE 
        WHEN current_liabilities = 0 THEN 0.0
        ELSE ROUND(CAST(current_assets AS REAL) / current_liabilities, 4)
    END AS current_liquidity_ratio
FROM balance_sheets
ORDER BY company_id, fiscal_year DESC;


-- QUERY 6: CASH GENERATION QUALITY - Net Income to Free Cash Flow (FCF) Convergence
-- Purpose: Cross-checks Child-to-Child financial tables to capture divergence in reported earnings.
SELECT 
    c.company_id,
    i.fiscal_year,
    i.net_income,
    cf.operating_cash_flow,
    cf.capital_expenditures,
    (cf.operating_cash_flow - cf.capital_expenditures) AS free_cash_flow,
    cf.operating_cash_flow - i.net_income AS cash_accrual_divergence
FROM companies c
JOIN income_statements i ON c.company_id = i.company_id
JOIN cash_flows cf ON c.company_id = cf.company_id AND i.fiscal_year = cf.fiscal_year
ORDER BY ABS(cash_accrual_divergence) DESC;


-- QUERY 7: MARKET CAPITALIZATION MATRIX - Dynamic Sizing Tiers via Volumetric Multipliers
-- Purpose: Tests real-time structural window ordering against pricing updates.
SELECT 
    c.company_id,
    c.company_name,
    m.fiscal_year,
    (m.closing_price * c.total_outstanding_shares) AS market_capitalization,
    CASE 
        WHEN (m.closing_price * c.total_outstanding_shares) >= 20000000000 THEN 'LARGE_CAP'
        WHEN (m.closing_price * c.total_outstanding_shares) >= 2000000000 THEN 'MID_CAP'
        ELSE 'SMALL_CAP'
    END AS enterprise_scale_classification
FROM companies c
JOIN market_prices m ON c.company_id = m.company_id
WHERE m.fiscal_year = (SELECT MAX(fiscal_year) FROM market_prices)
ORDER BY market_capitalization DESC;


-- QUERY 8: ALTERNATIVE SUPPLEMENTARY AUDIT - Credit Ratings vs. Leverage Coefficients
-- Purpose: Tests usability of Supplementary Sheet 2 data tied to the Core financial positions.
SELECT 
    c.company_id,
    r.credit_rating_agency,
    r.assigned_rating,
    b.fiscal_year,
    (b.total_liabilities / NULLIF(b.total_assets, 0)) AS total_debt_to_assets_leverage
FROM companies c
JOIN credit_ratings r ON c.company_id = r.company_id
JOIN balance_sheets b ON c.company_id = b.company_id AND r.rating_date_year = b.fiscal_year
ORDER BY total_debt_to_assets_leverage DESC;


-- QUERY 9: MACRO CONVERGENCE PROFILE - Sector Performance vs Gross Domestic Product (GDP) Swings
-- Purpose: Tests deep analytical multi-joins across core, sector, and macro indicators.
SELECT 
    s.sector_name,
    i.fiscal_year,
    AVG(i.total_revenue) AS average_sector_revenue,
    g.gdp_growth_rate,
    g.inflation_rate
FROM industry_sectors s
JOIN companies c ON s.sector_id = c.sector_id
JOIN income_statements i ON c.company_id = i.company_id
JOIN macro_indicators g ON i.fiscal_year = g.calendar_year
GROUP BY s.sector_name, i.fiscal_year
ORDER BY i.fiscal_year DESC, average_sector_revenue DESC;


-- QUERY 10: METADATA PIPELINE TRACKING - Integrity Audit on Multi-Sheet Loading Runs
-- Purpose: Validates that your child balance sheet records match active profiles in the parent system.
SELECT 
    'balance_sheets' AS verification_target_table,
    COUNT(b.company_id) AS total_rows_evaluated,
    COUNT(c.company_id) AS mapped_parent_rows,
    COUNT(b.company_id) - COUNT(c.company_id) AS orphan_foreign_key_violations
FROM balance_sheets b
LEFT JOIN companies c ON b.company_id = c.company_id;