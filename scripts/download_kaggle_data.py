import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sys
from src.data.downloader import download_dataset
from src.utils import logger

def main():
    logger.info("Starting Kaggle Dataset Download...")
    path = download_dataset(target_dir="data/raw")
    logger.info(f"Dataset ready at: {path}")

if __name__ == "__main__":
    main()
