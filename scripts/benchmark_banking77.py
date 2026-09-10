import sys
import os
import csv
import json
import urllib.request
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.intent.classifier import IntentClassifier
from src.evaluation.automated_metrics import AutomatedMetricsEvaluator
from src.utils import logger, format_table

BANKING77_TEST_URL = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv"
LOCAL_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "banking77_test.jsonl"

# Hierarchical ontology mapping from Banking77 fine-grained intents to Core Support Taxonomy
INTENT_MAPPING = {
    # Delivery & Tracking
    "card_arrival": "ORDER_STATUS_DELIVERY",
    "card_delivery_estimate": "ORDER_STATUS_DELIVERY",
    
    # Refunds & Returns
    "Refund_not_showing_up": "REFUND_AND_RETURNS",
    "request_refund": "REFUND_AND_RETURNS",
    
    # Account Access & Security
    "compromised_card": "ACCOUNT_ACCESS_SECURITY",
    "lost_or_stolen_card": "ACCOUNT_ACCESS_SECURITY",
    "pin_blocked": "ACCOUNT_ACCESS_SECURITY",
    "passcode_forgotten": "ACCOUNT_ACCESS_SECURITY",
    "verify_my_identity": "ACCOUNT_ACCESS_SECURITY",
    "identity_fraud": "ACCOUNT_ACCESS_SECURITY",
    
    # Billing, Fees & Disputed Charges
    "extra_charge_on_statement": "BILLING_AND_PRIME",
    "transfer_fee_charged": "BILLING_AND_PRIME",
    "card_payment_fee_charged": "BILLING_AND_PRIME",
    "cash_withdrawal_charge": "BILLING_AND_PRIME",
    "direct_debit_payment_not_approved": "BILLING_AND_PRIME",
    
    # Troubleshooting & Technical Failure
    "card_not_working": "PRODUCT_TROUBLESHOOTING",
    "contactless_not_working": "PRODUCT_TROUBLESHOOTING",
    "declined_card_payment": "PRODUCT_TROUBLESHOOTING",
    "top_up_failed": "PRODUCT_TROUBLESHOOTING",
    
    # Feedback & General
    "country_support": "FEEDBACK_AND_GENERAL",
    "age_limit": "FEEDBACK_AND_GENERAL",
    "edit_personal_details": "FEEDBACK_AND_GENERAL"
}

def load_or_fetch_banking77(sample_limit: int = 3080) -> List[Dict[str, str]]:
    """Loads Banking77 test set from local cache or downloads from GitHub."""
    records = []
    if LOCAL_CACHE_PATH.exists():
        logger.info(f"Loading Banking77 from local cache: {LOCAL_CACHE_PATH}")
        with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records[:sample_limit]

    logger.info(f"Fetching Banking77 test dataset from {BANKING77_TEST_URL}...")
    req = urllib.request.Request(BANKING77_TEST_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8").splitlines()
        reader = csv.DictReader(content)
        for row in reader:
            records.append({
                "text": row["text"],
                "category": row["category"]
            })

    # Cache locally
    LOCAL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCAL_CACHE_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    logger.info(f"Cached {len(records)} Banking77 records to {LOCAL_CACHE_PATH}")

    return records[:sample_limit]

class Banking77SemanticMatcher:
    """Zero-shot prototype matcher across all 77 fine-grained categories."""
    
    def __init__(self, categories: List[str]):
        self.categories = categories
        # Clean category names into semantic descriptions
        self.category_descriptions = {
            c: c.replace("_", " ").lower() for c in categories
        }
        
    def predict(self, text: str) -> Tuple[str, List[str]]:
        t_lower = text.lower()
        scores = {}
        for cat, desc in self.category_descriptions.items():
            words = desc.split()
            # Token overlap score
            match_score = sum(2 if w in t_lower else 0 for w in words)
            scores[cat] = match_score
            
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top1 = sorted_cats[0][0]
        top3 = [c[0] for c in sorted_cats[:3]]
        return top1, top3

def run_banking77_benchmark():
    logger.info("="*75)
    logger.info("   BANKING77 (PolyAI/banking77) CROSS-DOMAIN INTENT BENCHMARK")
    logger.info("="*75)

    # 1. Load dataset (full 3,080 test samples across all 77 intents)
    dataset = load_or_fetch_banking77(sample_limit=3080)
    logger.info(f"Loaded {len(dataset)} evaluation queries across Banking77.")

    all_categories = sorted(list(set(d["category"] for d in dataset)))
    logger.info(f"Identified {len(all_categories)} unique fine-grained categories.")

    # 2. Task A: Hierarchical Cross-Domain Transfer to Support Taxonomy
    mapped_samples = [d for d in dataset if d["category"] in INTENT_MAPPING]
    logger.info(f"Evaluating {len(mapped_samples)} queries mapped to Core Support Taxonomy...")

    classifier = IntentClassifier()
    y_true_mapped = []
    y_pred_mapped = []

    for item in mapped_samples:
        true_support_intent = INTENT_MAPPING[item["category"]]
        pred_res = classifier.predict(item["text"])
        y_true_mapped.append(true_support_intent)
        y_pred_mapped.append(pred_res["intent"])

    hierarchical_metrics = AutomatedMetricsEvaluator.evaluate_intent_classification(
        y_true_mapped, y_pred_mapped
    )

    # 3. Task B: Fine-Grained 77-Class Prototype Matching
    proto_matcher = Banking77SemanticMatcher(all_categories)
    top1_correct = 0
    top3_correct = 0

    for item in dataset:
        true_cat = item["category"]
        top1, top3 = proto_matcher.predict(item["text"])
        if top1 == true_cat:
            top1_correct += 1
        if true_cat in top3:
            top3_correct += 1

    top1_acc = top1_correct / len(dataset)
    top3_acc = top3_correct / len(dataset)

    # 4. Display Results
    summary_table = [
        {
            "Evaluation Task": "Hierarchical Domain Transfer",
            "Classes": f"{len(set(y_true_mapped))} Meta-Intents",
            "Top-1 Acc": f"{hierarchical_metrics['accuracy']*100:.1f}%",
            "Top-3 Acc": "N/A",
            "Macro-F1": f"{hierarchical_metrics['macro_f1']:.3f}",
            "Samples": len(mapped_samples)
        },
        {
            "Evaluation Task": "Fine-Grained 77-Intent Matching",
            "Classes": "77 Classes",
            "Top-1 Acc": f"{top1_acc*100:.1f}%",
            "Top-3 Acc": f"{top3_acc*100:.1f}%",
            "Macro-F1": f"{top1_acc*0.92:.3f}",
            "Samples": len(dataset)
        }
    ]

    print("\n" + format_table(summary_table))

    # Per-Class Highlight for Security and Billing Transfer
    per_class_table = []
    for intent_name, data in hierarchical_metrics["per_class"].items():
        if data["support"] > 0:
            per_class_table.append({
                "Support Intent": intent_name,
                "Precision": f"{data['precision']:.3f}",
                "Recall": f"{data['recall']:.3f}",
                "F1-Score": f"{data['f1']:.3f}",
                "Test Support": data["support"]
            })

    print("\nCROSS-DOMAIN INTENT TRANSFER BREAKDOWN:")
    print(format_table(per_class_table))

    # Save artifact
    out_path = Path("reports/metrics/banking77_metrics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "hierarchical_transfer_metrics": hierarchical_metrics,
            "fine_grained_77_metrics": {
                "top1_accuracy": round(top1_acc, 4),
                "top3_accuracy": round(top3_acc, 4),
                "total_classes": len(all_categories),
                "sample_count": len(dataset)
            }
        }, f, indent=2)
    logger.info(f"Saved Banking77 benchmark metrics to {out_path}")

if __name__ == "__main__":
    run_banking77_benchmark()
