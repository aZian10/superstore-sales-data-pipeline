"""Root entrypoint for running the end-to-end Superstore pipeline."""

import sys
from scripts.run_pipeline import run_pipeline

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
