import math
from typing import List, Dict, Any

class HumanJudgeAgreementAnalyzer:
    """Computes Cohen's Kappa, Pearson Correlation, and Inter-Rater metrics in pure Python."""

    @staticmethod
    def compute_agreement(human_scores: List[float], judge_scores: List[float]) -> Dict[str, Any]:
        n = len(human_scores)
        if n == 0:
            return {}

        h_int = [int(round(x)) for x in human_scores]
        j_int = [int(round(x)) for x in judge_scores]

        # Observed agreement Po
        po = sum(1 for h, j in zip(h_int, j_int) if h == j) / n

        # Expected agreement Pe
        all_categories = set(h_int).union(set(j_int))
        pe = 0.0
        for cat in all_categories:
            p_h = sum(1 for h in h_int if h == cat) / n
            p_j = sum(1 for j in j_int if j == cat) / n
            pe += (p_h * p_j)

        kappa = (po - pe) / (1.0 - pe) if (1.0 - pe) > 1e-6 else 1.0

        # Pearson Correlation
        mean_h = sum(human_scores) / n
        mean_j = sum(judge_scores) / n
        num = sum((h - mean_h) * (j - mean_j) for h, j in zip(human_scores, judge_scores))
        den_h = math.sqrt(sum((h - mean_h)**2 for h in human_scores))
        den_j = math.sqrt(sum((j - mean_j)**2 for j in judge_scores))
        
        pearson = num / (den_h * den_j) if (den_h * den_j) > 1e-6 else 1.0

        diffs = [abs(h - j) for h, j in zip(h_int, j_int)]
        exact_pct = (sum(1 for d in diffs if d == 0) / n) * 100.0
        adjacent_pct = (sum(1 for d in diffs if d <= 1) / n) * 100.0
        mae = sum(diffs) / n

        return {
            "cohen_kappa": round(kappa, 4),
            "pearson_correlation": round(pearson, 4),
            "exact_agreement_pct": round(exact_pct, 2),
            "adjacent_agreement_pct": round(adjacent_pct, 2),
            "mean_absolute_error": round(mae, 3),
            "sample_size": n
        }
