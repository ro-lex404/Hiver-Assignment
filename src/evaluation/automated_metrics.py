import math
from typing import List, Dict, Any
from src.intent.taxonomy import ALL_INTENTS

class AutomatedMetricsEvaluator:
    """Zero-dependency pure Python metric calculations for classification & escalation."""

    @staticmethod
    def evaluate_intent_classification(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
        total = max(len(y_true), 1)
        acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / total

        per_class = {}
        f1_list = []
        prec_list = []
        rec_list = []

        for intent in ALL_INTENTS:
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == intent and p == intent)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != intent and p == intent)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == intent and p != intent)
            support = sum(1 for t in y_true if t == intent)

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            per_class[intent] = {
                "precision": round(prec, 3),
                "recall": round(rec, 3),
                "f1": round(f1, 3),
                "support": support
            }
            if support > 0:
                f1_list.append(f1)
                prec_list.append(prec)
                rec_list.append(rec)

        macro_f1 = sum(f1_list) / max(len(f1_list), 1)
        macro_prec = sum(prec_list) / max(len(prec_list), 1)
        macro_rec = sum(rec_list) / max(len(rec_list), 1)

        return {
            "accuracy": round(acc, 4),
            "macro_precision": round(macro_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "macro_f1": round(macro_f1, 4),
            "per_class": per_class
        }

    @staticmethod
    def evaluate_escalation(y_true: List[bool], y_pred: List[bool]) -> Dict[str, Any]:
        total = max(len(y_true), 1)
        acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / total

        tp = sum(1 for t, p in zip(y_true, y_pred) if t is True and p is True)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t is False and p is True)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t is True and p is False)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t is False and p is False)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        return {
            "escalation_accuracy": round(acc, 4),
            "escalation_precision": round(prec, 4),
            "escalation_recall": round(rec, 4),
            "escalation_f1": round(f1, 4),
            "false_negatives": int(fn),
            "false_positives": int(fp)
        }

    @staticmethod
    def compute_lexical_similarity(predictions: List[str], references: List[str]) -> Dict[str, Any]:
        overlaps = []
        char_lengths = []
        within_twitter_limit = 0

        for pred, ref in zip(predictions, references):
            pred_tokens = set(pred.lower().split())
            ref_tokens = set(ref.lower().split())
            
            char_lengths.append(len(pred))
            if len(pred) <= 280:
                within_twitter_limit += 1

            if not ref_tokens:
                overlaps.append(0.0)
                continue

            jaccard = len(pred_tokens.intersection(ref_tokens)) / max(len(pred_tokens.union(ref_tokens)), 1)
            overlaps.append(jaccard)

        avg_overlap = sum(overlaps) / max(len(overlaps), 1)
        avg_len = sum(char_lengths) / max(len(char_lengths), 1)

        return {
            "mean_token_jaccard": round(avg_overlap, 4),
            "avg_char_length": round(avg_len, 1),
            "pct_within_280_chars": round((within_twitter_limit / max(len(predictions), 1)) * 100.0, 2)
        }
