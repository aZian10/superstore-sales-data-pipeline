"""Integration and data quality tests for PostgreSQL layers (Staging, Silver, Gold)."""

import pytest
import sqlalchemy as sa
from src.loading.db import get_engine


@pytest.fixture(scope="module")
def db_conn():
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


def test_schemas_exist(db_conn):
    """Verifies that all required schemas exist in the warehouse."""
    res = db_conn.execute(sa.text("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name IN ('raw', 'staging', 'silver', 'gold');
    """)).fetchall()
    found = {r[0] for r in res}
    assert found == {"raw", "staging", "silver", "gold"}


def test_row_counts_across_layers(db_conn):
    """Verifies row preservation from raw to staging to silver fact table."""
    raw_count = db_conn.execute(sa.text("SELECT COUNT(*) FROM raw.superstore;")).scalar()
    staging_count = db_conn.execute(sa.text("SELECT COUNT(*) FROM staging.superstore;")).scalar()
    fact_count = db_conn.execute(sa.text("SELECT COUNT(*) FROM silver.fact_sales;")).scalar()

    assert raw_count == 9994
    assert staging_count == 9994
    assert fact_count == 9994


def test_primary_key_uniqueness(db_conn):
    """Ensures absence of duplicate primary keys in dimensional and fact tables."""
    tables_pk = [
        ("staging", "superstore", "row_id"),
        ("silver", "customers", "customer_id"),
        ("silver", "products", "product_id"),
        ("silver", "fact_sales", "row_id"),
        ("gold", "daily_sales", "order_date"),
        ("gold", "product_performance", "product_id"),
        ("gold", "customer_performance", "customer_id"),
    ]

    for schema, table, pk in tables_pk:
        query = f"""
            SELECT {pk}, COUNT(*) 
            FROM {schema}.{table} 
            GROUP BY {pk} 
            HAVING COUNT(*) > 1;
        """
        duplicates = db_conn.execute(sa.text(query)).fetchall()
        assert len(duplicates) == 0, f"Found duplicate primary keys in {schema}.{table}"


def test_no_nulls_in_critical_fields(db_conn):
    """Ensures critical business fields have zero null values in silver fact."""
    null_count = db_conn.execute(sa.text("""
        SELECT COUNT(*) 
        FROM silver.fact_sales 
        WHERE order_id IS NULL 
           OR order_date IS NULL 
           OR customer_id IS NULL 
           OR product_id IS NULL 
           OR sales IS NULL 
           OR quantity IS NULL 
           OR profit IS NULL;
    """)).scalar()
    assert null_count == 0


def test_business_rules_integrity(db_conn):
    """Verifies domain rules: positive sales, positive quantity, valid days_to_ship."""
    invalid_rows = db_conn.execute(sa.text("""
        SELECT COUNT(*) 
        FROM silver.fact_sales 
        WHERE sales <= 0 
           OR quantity <= 0 
           OR days_to_ship < 0;
    """)).scalar()
    assert invalid_rows == 0


def test_gold_tables_not_empty(db_conn):
    """Verifies that all gold analytical datasets are populated."""
    gold_tables = [
        "daily_sales",
        "monthly_sales",
        "category_performance",
        "product_performance",
        "customer_performance",
        "regional_performance",
        "kpi_summary",
    ]

    for table in gold_tables:
        count = db_conn.execute(sa.text(f"SELECT COUNT(*) FROM gold.{table};")).scalar()
        assert count > 0, f"Gold table gold.{table} is unexpectedly empty"


def test_sales_and_profit_totals_consistency(db_conn):
    """Verifies mathematical consistency of totals between staging, silver, and gold."""
    staging_sales = float(db_conn.execute(sa.text("SELECT SUM(sales) FROM staging.superstore;")).scalar())
    silver_sales = float(db_conn.execute(sa.text("SELECT SUM(sales) FROM silver.fact_sales;")).scalar())
    gold_daily_sales = float(db_conn.execute(sa.text("SELECT SUM(total_sales) FROM gold.daily_sales;")).scalar())
    gold_monthly_sales = float(db_conn.execute(sa.text("SELECT SUM(total_sales) FROM gold.monthly_sales;")).scalar())

    assert abs(staging_sales - silver_sales) < 0.01
    assert abs(silver_sales - gold_daily_sales) < 1.0
    assert abs(gold_daily_sales - gold_monthly_sales) < 1.0


def test_kpi_summary_values(db_conn):
    """Validates executive KPI metrics calculation logic."""
    kpi_dict = dict(db_conn.execute(sa.text("SELECT metric_name, metric_value FROM gold.kpi_summary;")).fetchall())

    total_sales = float(kpi_dict["total_sales"])
    total_profit = float(kpi_dict["total_profit"])
    total_orders = int(kpi_dict["total_orders"])
    avg_order_value = float(kpi_dict["average_order_value"])
    profit_margin = float(kpi_dict["overall_profit_margin"])

    # Profit margin formula check: Total Profit / Total Sales * 100
    expected_margin = round((total_profit / total_sales) * 100, 2)
    assert abs(profit_margin - expected_margin) < 0.05

    # AOV formula check: Total Sales / Total Orders
    expected_aov = round(total_sales / total_orders, 2)
    assert abs(avg_order_value - expected_aov) < 0.05
