"""Apache Airflow DAG orchestrating the end-to-end Superstore data pipeline."""

from datetime import datetime, timedelta
import pytest
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

from src.ingestion.kaggle_downloader import ingest_superstore_data
from src.validation.validator import validate_raw_superstore
from src.loading.raw_loader import load_raw_superstore
from src.transformation.transformer import (
    transform_staging,
    build_silver,
    build_gold,
)
from src.utils.logger import get_logger

logger = get_logger("airflow_dag")

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=10),
}


def task_ingest():
    metadata = ingest_superstore_data()
    logger.info(f"Ingested {metadata['row_count']} rows from {metadata['source']}.")
    return metadata


def task_validate():
    report = validate_raw_superstore()
    if not report.is_valid:
        raise ValueError(
            f"Raw dataset validation failed with {report.invalid_rows} invalid rows."
        )
    logger.info(f"Validation passed: {report.valid_rows} valid records.")
    return report.valid_rows


def task_load_raw():
    rows_loaded = load_raw_superstore()
    logger.info(f"Loaded {rows_loaded} rows into raw.superstore.")
    return rows_loaded


def task_transform_staging():
    transform_staging()


def task_build_silver():
    build_silver()


def task_build_gold():
    build_gold()


def task_run_quality_tests():
    exit_code = pytest.main(["-v", "tests"])
    if exit_code != 0:
        raise RuntimeError(f"Automated data quality tests failed with exit code {exit_code}")
    logger.info("All data quality tests passed successfully.")


with DAG(
    dag_id="superstore_etl_pipeline",
    default_args=default_args,
    description="End-to-end Superstore pipeline: Ingestion -> Raw -> Staging -> Silver -> Gold -> Tests",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["superstore", "data_engineering", "portfolio"],
) as dag:

    download_dataset = PythonOperator(
        task_id="download_dataset",
        python_callable=task_ingest,
    )

    validate_raw_data = PythonOperator(
        task_id="validate_raw_data",
        python_callable=task_validate,
    )

    load_raw = PythonOperator(
        task_id="load_raw",
        python_callable=task_load_raw,
    )

    transform_staging_task = PythonOperator(
        task_id="transform_staging",
        python_callable=task_transform_staging,
    )

    build_silver_task = PythonOperator(
        task_id="build_silver",
        python_callable=task_build_silver,
    )

    build_gold_task = PythonOperator(
        task_id="build_gold",
        python_callable=task_build_gold,
    )

    run_quality_tests = PythonOperator(
        task_id="run_quality_tests",
        python_callable=task_run_quality_tests,
    )

    pipeline_success = EmptyOperator(
        task_id="pipeline_success",
    )

    (
        download_dataset
        >> validate_raw_data
        >> load_raw
        >> transform_staging_task
        >> build_silver_task
        >> build_gold_task
        >> run_quality_tests
        >> pipeline_success
    )
