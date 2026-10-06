"""Data validation module for Superstore raw data."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from src.utils.config import path_config
from src.utils.logger import get_logger

logger = get_logger("validation")

EXPECTED_COLUMNS = [
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
]

REQUIRED_NON_NULL_COLUMNS = [
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Customer ID",
    "Product ID",
    "Sales",
    "Quantity",
    "Profit",
]


@dataclass
class ValidationReport:
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    check_results: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    is_valid: bool = False

    def print_summary(self) -> None:
        status_icons = {True: "✓", False: "✗"}
        print("\n========================================")
        print("          VALIDATION RESULT             ")
        print("========================================")
        print(f"Rows checked:  {self.total_rows}")
        print(f"Valid rows:    {self.valid_rows}")
        print(f"Invalid rows:  {self.invalid_rows}")
        print("\nChecks:")
        for check, passed in self.check_results.items():
            print(f"{status_icons[passed]} {check}")
        print("========================================\n")


def validate_raw_superstore(
    input_path: Optional[Path] = None,
    error_output_path: Optional[Path] = None,
) -> ValidationReport:
    """Validates raw Superstore dataset against schema, domain, and integrity rules."""
    file_path = input_path or path_config.raw_data_path
    err_path = error_output_path or path_config.error_data_path

    logger.info(f"Starting data validation on {file_path}...")

    report = ValidationReport()

    if not file_path.exists():
        err_msg = f"Source file not found at {file_path}"
        logger.error(err_msg)
        report.errors.append(err_msg)
        report.check_results["File exists"] = False
        return report

    report.check_results["File exists"] = True

    # Read dataset
    try:
        df = pd.read_csv(file_path, encoding="windows-1252")
    except Exception as e:
        err_msg = f"Failed to parse CSV: {e}"
        logger.error(err_msg)
        report.errors.append(err_msg)
        report.check_results["Parse CSV"] = False
        return report

    report.total_rows = len(df)

    # 1. Schema check: Expected columns exist
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    report.check_results["Required columns"] = len(missing_cols) == 0
    if missing_cols:
        report.errors.append(f"Missing columns: {missing_cols}")

    # Track row-level invalidity mask
    rejection_reasons = pd.Series("", index=df.index)

    # 2. Null values in critical required columns
    for col in REQUIRED_NON_NULL_COLUMNS:
        if col in df.columns:
            null_mask = df[col].isnull()
            if null_mask.any():
                rejection_reasons[null_mask] += f"Null in {col}; "

    null_check_passed = not (df[REQUIRED_NON_NULL_COLUMNS].isnull().any().any())
    report.check_results["Null values"] = null_check_passed

    # 3. Data types and Numeric validity
    numeric_errors = False

    # Sales >= 0
    sales_num = pd.to_numeric(df["Sales"], errors="coerce")
    sales_invalid = sales_num.isnull() | (sales_num < 0)
    if sales_invalid.any():
        numeric_errors = True
        rejection_reasons[sales_invalid] += "Invalid Sales value; "

    # Quantity >= 1 integer
    qty_num = pd.to_numeric(df["Quantity"], errors="coerce")
    qty_invalid = qty_num.isnull() | (qty_num <= 0)
    if qty_invalid.any():
        numeric_errors = True
        rejection_reasons[qty_invalid] += "Invalid Quantity value; "

    # Discount between 0.0 and 1.0
    disc_num = pd.to_numeric(df["Discount"], errors="coerce")
    disc_invalid = disc_num.isnull() | (disc_num < 0) | (disc_num > 1.0)
    if disc_invalid.any():
        numeric_errors = True
        rejection_reasons[disc_invalid] += "Invalid Discount value; "

    # Profit must be valid numeric
    profit_num = pd.to_numeric(df["Profit"], errors="coerce")
    profit_invalid = profit_num.isnull()
    if profit_invalid.any():
        numeric_errors = True
        rejection_reasons[profit_invalid] += "Invalid Profit value; "

    report.check_results["Numeric values"] = not numeric_errors

    # 4. Dates parsing and consistency
    order_dt = pd.to_datetime(df["Order Date"], format="%m/%d/%Y", errors="coerce")
    ship_dt = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y", errors="coerce")

    date_parse_invalid = order_dt.isnull() | ship_dt.isnull()
    date_logic_invalid = ship_dt < order_dt
    dates_failed = date_parse_invalid | date_logic_invalid

    if dates_failed.any():
        rejection_reasons[dates_failed] += "Invalid or inconsistent dates; "

    report.check_results["Dates"] = not dates_failed.any()

    # 5. Duplicate Row ID check
    duplicate_ids = df["Row ID"].duplicated()
    if duplicate_ids.any():
        rejection_reasons[duplicate_ids] += "Duplicate Row ID; "

    report.check_results["Duplicate IDs"] = not duplicate_ids.any()

    # 6. Overall data types check
    report.check_results["Data types"] = (
        report.check_results["Numeric values"] and report.check_results["Dates"]
    )

    # Separate valid and invalid rows
    invalid_mask = rejection_reasons != ""
    report.invalid_rows = int(invalid_mask.sum())
    report.valid_rows = report.total_rows - report.invalid_rows

    if report.invalid_rows > 0:
        err_df = df[invalid_mask].copy()
        err_df["rejection_reason"] = rejection_reasons[invalid_mask]
        err_path.parent.mkdir(parents=True, exist_ok=True)
        err_df.to_csv(err_path, index=False, encoding="utf-8")
        logger.warning(f"Saved {report.invalid_rows} invalid rows to {err_path}")
    else:
        logger.info("Validation successful: 0 invalid rows found.")

    report.is_valid = (
        report.invalid_rows == 0
        and all(report.check_results.values())
    )

    report.print_summary()
    return report


if __name__ == "__main__":
    validate_raw_superstore()
