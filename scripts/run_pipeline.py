"""End-to-end data pipeline runner executing ingestion, validation, loading, transformations, and testing."""

import sys
import pytest
from src.utils.logger import get_logger
from src.ingestion.kaggle_downloader import ingest_superstore_data
from src.validation.validator import validate_raw_superstore
from src.loading.raw_loader import load_raw_superstore
from src.transformation.transformer import transform_staging, build_silver, build_gold

logger = get_logger("pipeline_runner")


def run_pipeline() -> bool:
    """Executes the complete Superstore data engineering workflow."""
    logger.info("==================================================")
    logger.info("Starting Superstore End-to-End Data Pipeline")
    logger.info("==================================================")

    # 1. Ingestion
    logger.info("Step 1/6: Ingesting dataset...")
    metadata = ingest_superstore_data()
    logger.info(f"Ingestion completed. Rows detected: {metadata['row_count']}")

    # 2. Validation
    logger.info("Step 2/6: Validating raw data...")
    val_report = validate_raw_superstore()
    if not val_report.is_valid:
        logger.error(f"Validation failed with {val_report.invalid_rows} invalid rows. Aborting pipeline.")
        return False
    logger.info("Validation passed successfully.")

    # 3. Raw Loading
    logger.info("Step 3/6: Loading raw data into PostgreSQL raw.superstore...")
    raw_rows = load_raw_superstore()
    logger.info(f"Raw table loaded: {raw_rows} rows.")

    # 4. Staging Transformation
    logger.info("Step 4/6: Standardizing data in staging.superstore...")
    transform_staging()
    logger.info("Staging transformation completed.")

    # 5. Silver Layer Build
    logger.info("Step 5/6: Building Silver dimensional model...")
    build_silver()
    logger.info("Silver transformation completed.")

    # 6. Gold Layer Build
    logger.info("Step 6/6: Generating Gold analytical datasets and KPIs...")
    build_gold()
    logger.info("Gold tables created.")

    # 7. Automated Quality Testing
    logger.info("Running automated data quality tests...")
    test_exit_code = pytest.main(["-v", "tests"])
    if test_exit_code != 0:
        logger.error(f"Data quality tests failed with exit code {test_exit_code}.")
        return False

    logger.info("Quality tests passed.")
    logger.info("==================================================")
    logger.info("Pipeline executed successfully and idempotently!")
    logger.info("==================================================")
    return True


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
