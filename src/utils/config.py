"""Configuration management module for the data pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "superstore")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")

    @property
    def connection_uri(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class PathConfig:
    root: Path = ROOT_DIR
    raw_data_path: Path = ROOT_DIR / os.getenv("RAW_DATA_PATH", "data/raw/superstore.csv")
    processed_data_path: Path = ROOT_DIR / os.getenv("PROCESSED_DATA_PATH", "data/processed/superstore_cleaned.csv")
    error_data_path: Path = ROOT_DIR / os.getenv("ERROR_DATA_PATH", "data/errors/superstore_invalid.csv")
    metadata_path: Path = ROOT_DIR / "data/raw/metadata.json"
    sql_dir: Path = ROOT_DIR / "sql"


@dataclass(frozen=True)
class KaggleConfig:
    username: str = os.getenv("KAGGLE_USERNAME", "")
    key: str = os.getenv("KAGGLE_KEY", "")
    dataset: str = os.getenv("KAGGLE_DATASET", "vivek468/superstore-dataset-final")


db_config = DatabaseConfig()
path_config = PathConfig()
kaggle_config = KaggleConfig()
