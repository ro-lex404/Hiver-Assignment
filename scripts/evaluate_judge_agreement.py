import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
from pathlib import Path

from src.evaluation.llm_judge import LLMJudgeRubric
from src.evaluation.agreement import HumanJudgeAgreementAnalyzer
from src.utils import logger

def main():
    calib_path = "data/golden_set/human_judge_calibration_50.jsonl"
    records = []
    with open(calib_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    logger.info(f"Loaded {len(records)} human calibration samples.")

    judge = LLMJudgeRubric()
    human_overall = []
    judge_overall = []
    
    dim_scores = {
        "groundedness": {"human": [], "judge": []},
        "helpfulness": {"human": [], "judge": []},
        "tone_safety": {"human": [], "judge": []},
        "escalation_appropriateness": {"human": [], "judge": []}
    }

    for item in records:
        h_ratings = item["human_ratings"]
        human_overall.append(h_ratings["overall_quality"])
        
        # Run judge on the reference reply / gold scenario
        j_res = judge.evaluate_reply(
            customer_text=item["text"],
            predicted_reply=item["reference_reply"],
            predicted_intent=item["true_intent"],
            predicted_escalation=False,
            true_intent=item["true_intent"],
            true_escalation=False,
            reference_reply=item["reference_reply"]
        )
        judge_overall.append(j_res["overall_score"])

        for dim in dim_scores:
            dim_scores[dim]["human"].append(h_ratings[dim])
            dim_scores[dim]["judge"].append(j_res[dim])

    agreement_summary = HumanJudgeAgreementAnalyzer.compute_agreement(human_overall, judge_overall)

    print("\n" + "="*70)
    print("        HUMAN vs. LLM-AS-A-JUDGE CALIBRATION & AGREEMENT STUDY")
    print("="*70)
    for k, v in agreement_summary.items():
        print(f"  {k:30s} : {v}")
    print("="*70)

    # Save to metrics
    out_dir = Path("reports/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "judge_agreement.json").write_text(json.dumps(agreement_summary, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
