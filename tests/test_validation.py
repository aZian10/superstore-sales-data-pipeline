"""Unit tests for the raw data validation module."""

from pathlib import Path
import pandas as pd
import pytest

from src.validation.validator import validate_raw_superstore, EXPECTED_COLUMNS
from src.utils.config import path_config


def test_raw_file_validation_passes_on_canonical_data():
    """Validates that canonical Superstore raw data passes all checks without invalid rows."""
    assert path_config.raw_data_path.exists(), "Raw data file must exist"
    report = validate_raw_superstore(path_config.raw_data_path)

    assert report.is_valid is True
    assert report.total_rows == 9994
    assert report.valid_rows == 9994
    assert report.invalid_rows == 0
    assert report.check_results["Required columns"] is True
    assert report.check_results["Null values"] is True
    assert report.check_results["Numeric values"] is True
    assert report.check_results["Dates"] is True
    assert report.check_results["Duplicate IDs"] is True


def test_validator_rejects_corrupted_records(tmp_path: Path):
    """Verifies that corrupted records (bad dates, negative sales, zero quantity) are isolated."""
    corrupted_data = pd.DataFrame({
        "Row ID": [1, 2, 2],  # Duplicate Row ID
        "Order ID": ["CA-2016-001", "CA-2016-002", "CA-2016-003"],
        "Order Date": ["11/08/2016", "99/99/9999", "11/08/2016"],  # Impossible date
        "Ship Date": ["11/05/2016", "11/12/2016", "11/12/2016"],   # Ship Date < Order Date
        "Ship Mode": ["Standard", "Standard", "Standard"],
        "Customer ID": ["CG-12520", "CG-12520", None],            # Null customer ID
        "Customer Name": ["Claire Gute", "Claire Gute", "Claire Gute"],
        "Segment": ["Consumer", "Consumer", "Consumer"],
        "Country": ["United States", "United States", "United States"],
        "City": ["Henderson", "Henderson", "Henderson"],
        "State": ["Kentucky", "Kentucky", "Kentucky"],
        "Postal Code": [42420, 42420, 42420],
        "Region": ["South", "South", "South"],
        "Product ID": ["FUR-BO-10001798", "FUR-BO-10001798", "FUR-BO-10001798"],
        "Category": ["Furniture", "Furniture", "Furniture"],
        "Sub-Category": ["Bookcases", "Bookcases", "Bookcases"],
        "Product Name": ["Bush Somerset Bookcase", "Bush Somerset Bookcase", "Bush Somerset Bookcase"],
        "Sales": [261.96, -50.0, 100.0],                          # Negative sales
        "Quantity": [2, 0, 3],                                     # Zero quantity
        "Discount": [0.0, 1.5, 0.2],                               # Discount > 1.0
        "Profit": [41.91, 10.0, 20.0],
    })

    test_csv = tmp_path / "corrupted.csv"
    test_err_csv = tmp_path / "errors.csv"
    corrupted_data.to_csv(test_csv, index=False)

    report = validate_raw_superstore(test_csv, error_output_path=test_err_csv)

    assert report.is_valid is False
    assert report.invalid_rows > 0
    assert test_err_csv.exists()

    err_df = pd.read_csv(test_err_csv)
    assert "rejection_reason" in err_df.columns
