"""Loader module for loading original Superstore data into raw.superstore."""

from pathlib import Path
from typing import Optional
import pandas as pd
import sqlalchemy as sa

from src.loading.db import get_engine, get_connection
from src.utils.config import path_config
from src.utils.logger import get_logger

logger = get_logger("raw_loader")


def load_raw_superstore(csv_path: Optional[Path] = None) -> int:
    """Loads validated raw CSV into PostgreSQL raw.superstore.

    Maintains source structure faithfully and ensures idempotency.
    """
    file_path = csv_path or path_config.raw_data_path

    if not file_path.exists():
        raise FileNotFoundError(f"Raw CSV file not found: {file_path}")

    logger.info(f"Loading raw data from {file_path} into raw.superstore...")

    df = pd.read_csv(file_path, encoding="windows-1252")
    engine = get_engine()

    # Ensure schema raw exists
    with get_connection() as conn:
        conn.execute(sa.text("CREATE SCHEMA IF NOT EXISTS raw;"))

    # Load data into raw.superstore using replace for idempotency
    df.to_sql(
        name="superstore",
        con=engine,
        schema="raw",
        if_exists="replace",
        index=False,
        chunksize=2000,
        dtype={
            "Row ID": sa.types.Integer(),
            "Order ID": sa.types.VARCHAR(50),
            "Order Date": sa.types.VARCHAR(20),
            "Ship Date": sa.types.VARCHAR(20),
            "Ship Mode": sa.types.VARCHAR(50),
            "Customer ID": sa.types.VARCHAR(50),
            "Customer Name": sa.types.VARCHAR(150),
            "Segment": sa.types.VARCHAR(50),
            "Country": sa.types.VARCHAR(50),
            "City": sa.types.VARCHAR(100),
            "State": sa.types.VARCHAR(100),
            "Postal Code": sa.types.VARCHAR(20),
            "Region": sa.types.VARCHAR(50),
            "Product ID": sa.types.VARCHAR(50),
            "Category": sa.types.VARCHAR(100),
            "Sub-Category": sa.types.VARCHAR(100),
            "Product Name": sa.types.Text(),
            "Sales": sa.types.Numeric(12, 4),
            "Quantity": sa.types.Integer(),
            "Discount": sa.types.Numeric(5, 4),
            "Profit": sa.types.Numeric(12, 4),
        },
    )

    with get_connection() as conn:
        count = conn.execute(sa.text("SELECT COUNT(*) FROM raw.superstore;")).scalar()

    logger.info(f"Successfully loaded {count} rows into raw.superstore.")
    return int(count)


if __name__ == "__main__":
    load_raw_superstore()
