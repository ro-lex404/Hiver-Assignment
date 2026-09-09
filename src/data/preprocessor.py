import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from src.utils import clean_tweet_text, logger

class TwitterDataPreprocessor:
    """Preprocesses raw Twitter support CSV into structured conversation pairs for RAG & evaluation."""

    def __init__(self, target_brand: str = "AmazonHelp"):
        self.target_brand = target_brand

    def filter_brand_conversations(self, csv_path: str) -> pd.DataFrame:
        """Filter tweets for target brand and reconstruct QA pairs."""
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from {csv_path}")
        
        # Identify brand responses
        brand_mask = df["author_id"].str.lower() == self.target_brand.lower()
        brand_tweets = df[brand_mask]
        
        # Match with in_response_to customer tweets
        merged = df.merge(
            brand_tweets,
            left_on="tweet_id",
            right_on="in_response_to_tweet_id",
            suffixes=("_customer", "_agent")
        )
        
        logger.info(f"Extracted {len(merged)} agent-customer resolution pairs for {self.target_brand}")
        return merged

    def build_knowledge_base(self, qa_df: pd.DataFrame, max_samples: int = 500) -> List[Dict[str, str]]:
        """Transform QA DataFrame into indexed resolution memory for RAG."""
        kb = []
        for _, row in qa_df.head(max_samples).iterrows():
            customer_text = clean_tweet_text(str(row.get("text_customer", "")))
            agent_text = clean_tweet_text(str(row.get("text_agent", "")))
            
            if customer_text and agent_text:
                kb.append({
                    "query": customer_text,
                    "resolution": agent_text,
                    "brand": self.target_brand
                })
        return kb
