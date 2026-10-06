"""Database transformation coordinator executing Staging, Silver, and Gold transformations."""

from src.loading.db import execute_sql_file
from src.utils.config import path_config
from src.utils.logger import get_logger

logger = get_logger("transformation")


def transform_staging() -> None:
    """Executes staging schema DDL and idempotent data load."""
    logger.info("Starting Staging layer transformation...")
    sql_dir = path_config.sql_dir / "staging"
    execute_sql_file(str(sql_dir / "01_create_staging.sql"))
    execute_sql_file(str(sql_dir / "02_load_staging.sql"))
    logger.info("Staging transformation completed successfully.")


def build_silver() -> None:
    """Executes silver schema DDL and dimensional entity load."""
    logger.info("Starting Silver layer transformation...")
    sql_dir = path_config.sql_dir / "silver"
    execute_sql_file(str(sql_dir / "01_create_silver.sql"))
    execute_sql_file(str(sql_dir / "02_load_silver.sql"))
    logger.info("Silver transformation completed successfully.")


def build_gold() -> None:
    """Executes gold schema DDL and analytical KPI aggregations."""
    logger.info("Starting Gold layer transformation...")
    sql_dir = path_config.sql_dir / "gold"
    execute_sql_file(str(sql_dir / "01_create_gold.sql"))
    execute_sql_file(str(sql_dir / "02_load_gold.sql"))
    logger.info("Gold transformation completed successfully.")


def run_all_transformations() -> None:
    """Runs all transformation stages in dependency order."""
    transform_staging()
    build_silver()
    build_gold()


if __name__ == "__main__":
    run_all_transformations()
