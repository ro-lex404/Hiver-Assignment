import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import os
import json
from pathlib import Path
from src.utils import logger

def prepare_kaggle_kernel_metadata(
    kernel_slug: str = "hiver-ai-customer-support-agent",
    title: str = "Hiver AI Customer Support Agent & Evaluation Benchmark",
    code_file: str = "scripts/run_evaluation.py"
):
    metadata = {
        "id": f"{os.getenv('KAGGLE_USERNAME', 'candidate')}/{kernel_slug}",
        "title": title,
        "code_file": code_file,
        "language": "python",
        "kernel_type": "script",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_internet": "true",
        "dataset_sources": [
            "thoughtvector/customer-support-on-twitter"
        ],
        "competition_sources": [],
        "kernel_sources": []
    }
    
    meta_path = Path("kernel-metadata.json")
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info(f"Generated Kaggle kernel metadata at {meta_path}")
    return meta_path

def push_to_kaggle():
    meta_path = prepare_kaggle_kernel_metadata()
    try:
        import kaggle
        logger.info("Pushing code to Kaggle kernel...")
        kaggle.api.kernel_push(str(Path(".").resolve()))
        logger.info("Successfully pushed to Kaggle!")
    except Exception as e:
        logger.warning(f"Kaggle push skipped (install kaggle CLI or provide KAGGLE_KEY): {e}")

if __name__ == "__main__":
    push_to_kaggle()
