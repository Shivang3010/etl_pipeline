import pytest
from src.etl.normaliser import normalize_year, normalize_ticker

# =====================================================================
# PART 1: NORMALIZE_YEAR UNIT TEST VARIATIONS (21 Cases Total)
# =====================================================================

@pytest.mark.parametrize(
    "valid_input, expected_year",
    [
        # Standard structural string forms (5 tests)
        ("2023", 2023),
        ("1999", 1999),
        ("  2026  ", 2026),  # Trailing/leading spaces
        ("2030", 2030),
        ("1905", 1905),
        # Financial / Fiscal Year variants (5 tests)
        ("FY 2023-24", 2023),
        ("FY 1998-99", 1998),
        ("AY 2025/26", 2025),
        ("Financial Year 2021", 2021),
        ("CY2022", 2022),
        # ISO / Timestamps & Long Date strings (6 tests)
        ("2024-11-14 08:30:00", 2024),
        ("2020/01/01", 2020),
        ("1995-12-25T14:23:11Z", 1995),
        ("2023.05.12", 2023),
        ("Collected in 2018 on-site", 2018),
        ("2026-06-19", 2026),
        # Native Numeric Types (2 tests)
        (2021, 2021),
        (1984, 1984),
    ]
)
def test_normalize_year_valid_cases(valid_input, expected_year):
    """Verifies normalize_year properly handles clean and multi-format valid strings."""
    assert normalize_year(valid_input) == expected_year


@pytest.mark.parametrize(
    "invalid_input",
    [
        (""),                 # Empty string edge case
        ("   "),              # Whitespace only edge case
        ("ABC-DEF"),          # No numbers at all
        ("-2023"),            # Negative value prefix
        ("23"),               # Only 2 digits (ambiguous)
        ("12345"),            # 5 digits out-of-bounds
        ("1899"),             # Out of modern boundary range (< 1900)
        ("2101"),             # Out of modern boundary range (> 2100)
        (None),               # Null values edge case
    ]
)
def test_normalize_year_exceptions(invalid_input):
    """Verifies normalize_year explicitly raises ValueError for nulls, negatives, and bad shapes."""
    with pytest.raises(ValueError):
        normalize_year(invalid_input)


# =====================================================================
# PART 2: NORMALIZE_TICKER UNIT TEST VARIATIONS (16 Cases Total)
# =====================================================================

@pytest.mark.parametrize(
    "ticker_input, expected_ticker",
    [
        # Standard strings and casing (4 tests)
        ("tcs", "TCS"),
        ("AAPL", "AAPL"),
        ("  infy  ", "INFY"),       # Trailing / leading spaces
        ("msft", "MSFT"),
        # Internal space anomalies (3 tests)
        ("brk b", "BRKB"),
        ("m and m", "MANDM"),
        (" b a  e ", "BAE"),
        # Regional Exchange Suffix structural splits via Dot (5 tests)
        ("RELIANCE.NS", "RELIANCE"),
        ("TCS.BOM", "TCS"),
        ("SAP.DE", "SAP"),
        ("BP.L", "BP"),
        ("GOOG.O", "GOOG"),
        # Regional Exchange Suffix structural splits via Colon (2 tests)
        ("TSLA:US", "TSLA"),
        ("7203:JP", "7203"),        # Numerical tickers like Japan
        # Special edge case values (2 tests)
        ("", ""),                   # Empty string mapping
        (None, ""),                 # Null values translation mapping
    ]
)
def test_normalize_ticker_cases(ticker_input, expected_ticker):
    """Verifies normalize_ticker uniformly strips space, targets uppercase, and drops suffixes."""
    assert normalize_ticker(ticker_input) == expected_ticker
    