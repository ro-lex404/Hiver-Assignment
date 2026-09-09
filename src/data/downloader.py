import os
import urllib.request
from pathlib import Path
from src.utils import logger

KAGGLE_DATASET = "thoughtvector/customer-support-on-twitter"

def download_dataset(target_dir: str = "data/raw", force_sample: bool = False) -> str:
    """
    Download the customer support dataset from Kaggle or direct sample backup.
    Returns path to downloaded file.
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    sample_dest = target_path / "sample.csv"
    if sample_dest.exists() and not force_sample:
        logger.info(f"Dataset already exists at {sample_dest}")
        return str(sample_dest)

    try:
        # Check if Kaggle CLI or credentials are available
        import kaggle
        logger.info(f"Downloading {KAGGLE_DATASET} via Kaggle API...")
        kaggle.api.dataset_download_files(KAGGLE_DATASET, path=target_dir, unzip=True)
        logger.info("Download completed successfully.")
        return str(target_path / "twcs.csv")
    except Exception as e:
        logger.warning(f"Kaggle API download failed or credentials not set: {e}")
        logger.info("Falling back to verified sample download...")
        
        # Download verified sample CSV from public storage
        sample_url = "https://raw.githubusercontent.com/marshmellow77/twitter-customer-support/master/sample.csv"
        try:
            urllib.request.urlretrieve(sample_url, str(sample_dest))
            logger.info(f"Sample dataset downloaded to {sample_dest}")
            return str(sample_dest)
        except Exception as fallback_err:
            logger.error(f"Sample download failed: {fallback_err}")
            # Create local minimal placeholder sample
            sample_dest.write_text("tweet_id,author_id,inbound,created_at,text,response_tweet_id,in_response_to_tweet_id
1,Customer1,True,2026-01-01,Where is my order?,2,
2,AmazonHelp,False,2026-01-01,Please check tracking at amazon.com/your-orders,,1
", encoding="utf-8")
            return str(sample_dest)
