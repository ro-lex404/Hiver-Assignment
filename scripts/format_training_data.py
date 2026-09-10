import json
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.intent.classifier import IntentClassifier
from src.escalation.engine import EscalationEngine
from src.utils import clean_tweet_text, logger

def format_conversations(
    input_path: str = "data/processed/amazon_qa_english_5k.jsonl",
    output_path: str = "data/processed/amazon_conversations_formatted.jsonl",
    max_samples: int = 5000
):
    in_file = Path(input_path)
    out_file = Path(output_path)
    
    if not in_file.exists():
        logger.error(f"Input file not found: {in_file}")
        return

    classifier = IntentClassifier()
    escalation_engine = EscalationEngine()

    system_prompt = (
        "You are the official customer service AI agent for @AmazonHelp. "
        "Provide polite, empathetic, concise support replies strictly under 280 characters aligned with Amazon SOPs."
    )

    formatted_records = []
    logger.info(f"Formatting up to {max_samples:,} pairs from {in_file.name} into conversational schema...")

    with open(in_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= max_samples:
                break
            item = json.loads(line)
            
            raw_query = item.get("query", "")
            raw_resolution = item.get("resolution", "")
            
            clean_query = clean_tweet_text(raw_query)
            clean_resolution = clean_tweet_text(raw_resolution)

            # Auto-tag intent & escalation metadata using pipeline models
            intent_res = classifier.predict(clean_query)
            intent = intent_res["intent"]
            confidence = intent_res["confidence"]
            
            esc_res = escalation_engine.evaluate(clean_query, intent, confidence)

            record = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": clean_query},
                    {"role": "assistant", "content": clean_resolution}
                ],
                "metadata": {
                    "intent": intent,
                    "confidence": confidence,
                    "escalation": esc_res["should_escalate"],
                    "stated_reason": esc_res["stated_reason"],
                    "risk_score": esc_res["risk_score"],
                    "customer_tweet_id": item.get("customer_tweet_id", ""),
                    "agent_tweet_id": item.get("agent_tweet_id", "")
                }
            }
            formatted_records.append(record)

    with open(out_file, "w", encoding="utf-8") as f:
        for r in formatted_records:
            f.write(json.dumps(r) + "\n")

    logger.info(f"Successfully generated {len(formatted_records):,} formatted conversational records in {out_file}")

if __name__ == "__main__":
    format_conversations()
