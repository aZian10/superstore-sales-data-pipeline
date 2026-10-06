"""Ingestion module for acquiring the Superstore dataset and recording metadata."""

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from src.utils.config import kaggle_config, path_config
from src.utils.logger import get_logger

logger = get_logger("ingestion")


def calculate_sha256(file_path: Path) -> str:
    """Calculates SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_lines(file_path: Path) -> int:
    """Counts data rows in a CSV file (excluding header)."""
    with open(file_path, "r", encoding="windows-1252", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)


def download_from_kaggle(dataset_slug: str, download_dir: Path) -> Path:
    """Downloads dataset using Kaggle API if credentials are provided."""
    # Ensure environment variables are propagated to kaggle library
    if kaggle_config.username and kaggle_config.key:
        os.environ["KAGGLE_USERNAME"] = kaggle_config.username
        os.environ["KAGGLE_KEY"] = kaggle_config.key

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    logger.info(f"Authenticated with Kaggle API as {kaggle_config.username or 'local user'}")

    download_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading dataset '{dataset_slug}' into {download_dir}...")
    api.dataset_download_files(dataset_slug, path=str(download_dir), unzip=True)

    # Locate CSV file
    csv_candidates = list(download_dir.glob("*.csv"))
    if not csv_candidates:
        raise FileNotFoundError(f"No CSV file extracted from Kaggle dataset '{dataset_slug}'")

    # Prefer Sample - Superstore.csv or superstore.csv
    target_csv = None
    for candidate in csv_candidates:
        if "superstore" in candidate.name.lower():
            target_csv = candidate
            break
    if not target_csv:
        target_csv = csv_candidates[0]

    return target_csv


def download_from_fallback_url(target_path: Path) -> None:
    """Downloads the canonical 9,994-row dataset from verified public mirror."""
    import urllib.request
    url = "https://raw.githubusercontent.com/suyog2001/Tableau_Superstore_Sales_Dashboard/main/Sample%20-%20Superstore.csv"
    logger.info(f"Downloading canonical dataset from fallback mirror: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response, open(target_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


def ingest_superstore_data(force_download: bool = False) -> Dict[str, Any]:
    """Coordinates data ingestion: Kaggle API -> Local verification -> Metadata generation."""
    logger.info("Starting ingestion stage...")
    raw_path = path_config.raw_data_path
    raw_dir = raw_path.parent
    raw_dir.mkdir(parents=True, exist_ok=True)

    source_used = "local_cache"

    # Attempt download from Kaggle if forced or raw file missing
    if force_download or not raw_path.exists():
        has_credentials = bool(kaggle_config.username and kaggle_config.key) or (
            Path.home() / ".kaggle" / "kaggle.json"
        ).exists()

        if has_credentials:
            try:
                temp_extract = raw_dir / "_temp_kaggle"
                extracted_csv = download_from_kaggle(kaggle_config.dataset, temp_extract)
                shutil.copy2(extracted_csv, raw_path)
                shutil.rmtree(temp_extract, ignore_errors=True)
                source_used = f"kaggle:{kaggle_config.dataset}"
                logger.info(f"Successfully downloaded and saved raw data to {raw_path}")
            except Exception as e:
                logger.warning(f"Kaggle download failed ({e}). Checking local/mirror fallback.")
                if not raw_path.exists():
                    download_from_fallback_url(raw_path)
                    source_used = "mirror:github"
        else:
            if not raw_path.exists():
                logger.info("Kaggle credentials not provided. Fetching canonical dataset from public mirror.")
                download_from_fallback_url(raw_path)
                source_used = "mirror:github"
            else:
                logger.info(f"Using pre-existing raw file at {raw_path}")
    else:
        logger.info(f"Raw file already present at {raw_path}. Skipping download.")

    if not raw_path.exists() or raw_path.stat().st_size == 0:
        raise RuntimeError(f"Raw data file {raw_path} does not exist or is empty.")

    # Record metadata
    file_stat = raw_path.stat()
    row_count = count_lines(raw_path)
    checksum = calculate_sha256(raw_path)

    metadata = {
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source_used,
        "file_name": raw_path.name,
        "file_size_bytes": file_stat.st_size,
        "row_count": row_count,
        "sha256_checksum": checksum,
    }

    with open(path_config.metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(
        f"Ingestion completed: {raw_path.name} ({file_stat.st_size} bytes, "
        f"{row_count} rows, checksum: {checksum[:12]}...)"
    )
    return metadata


if __name__ == "__main__":
    ingest_superstore_data()
