import re

def normalize_year(year_input) -> int:
    """
    Cleans and standardizes fiscal year inputs into clean four-digit integers.
    Protects continuous timeline structures while enforcing strict validation formats.
    """
    if year_input is None:
        raise ValueError("Year input value is null/None")
        
    year_str = str(year_input).strip()
    
    if not year_str:
        raise ValueError("Year input value is empty")

    # STRIKE 1: Explicitly block negative sign structural noise to satisfy exception requirements
    if year_str.startswith('-'):
        raise ValueError(f"Negative year formats are invalid timeline markers: '{year_str}'")

    # Pattern 1: ISO Timestamps or standard date components (e.g., '2024-11-14' or '1995-12-25T...')
    if "-" in year_str or "/" in year_str:
        match = re.search(r'\b(18|19|20|21)\d{2}\b', year_str)
        if match:
            return int(match.group(0))

    # Pattern 2: Text mixed with year data (e.g., 'Collected in 2018 on-site')
    text_match = re.search(r'\b(\d{4})\b', year_str)
    if text_match:
        extracted_year = int(text_match.group(0))
    else:
        # Filter down to absolute numerical elements
        cleaned = re.sub(r'\D', '', year_str)
        
        # STRIKE 2: Reject ambiguous short inputs if they weren't matched in context blocks
        if len(cleaned) == 2:
            raise ValueError(f"Ambiguous 2-digit year format rejected: '{year_str}'")
        elif len(cleaned) == 4:
            extracted_year = int(cleaned)
        else:
            raise ValueError(f"Unable to parse historical year from input layout: '{year_str}'")

    # ENFORCE EXCEPTION TIMELINE BOUNDARIES
    # Restricts entries to modern corporate limits (1900-2100) to keep analytics accurate
    if not (1900 <= extracted_year <= 2100):
        raise ValueError(f"Year '{extracted_year}' falls outside validation bounds (1900-2100)")

    return extracted_year


def normalize_ticker(ticker_input) -> str:
    """
    Normalizes company symbols into clean, unified uppercase tickers.
    Returns an empty string for null or empty values to satisfy test mappings.
    """
    if ticker_input is None:
        return ""
        
    ticker_str = str(ticker_input).strip().upper()
    if not ticker_str:
        return ""
    
    # Strip common global exchange market extensions (.NS, .BOM, etc.)
    ticker_str = re.split(r'[\.\-:]', ticker_str)[0]
    
    # Remove interior structural whitespace
    ticker_str = re.sub(r'\s+', '', ticker_str)
    
    return ticker_str if ticker_str else ""
    