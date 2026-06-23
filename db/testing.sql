SELECT company_id, COUNT(DISTINCT fiscal_year) as history_window, MIN(fiscal_year), MAX(fiscal_year)
FROM balance_sheets
GROUP BY company_id
ORDER BY RANDOM()
LIMIT 5;