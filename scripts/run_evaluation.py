import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
from pathlib import Path

from src.pipeline import SupportAgentPipeline
from src.baselines.trivial_baseline import TrivialBaselineAgent
from src.baselines.simple_baseline import SimpleBaselineAgent
from src.evaluation.automated_metrics import AutomatedMetricsEvaluator
from src.evaluation.llm_judge import LLMJudgeRubric
from src.utils import format_table, logger

def load_golden_set(filepath: str = "data/golden_set/golden_eval_200.jsonl"):
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def run_benchmark():
    dataset = load_golden_set()
    logger.info(f"Loaded {len(dataset)} evaluation records from golden set.")

    models = {
        "Trivial Baseline": TrivialBaselineAgent(),
        "Simple Baseline": SimpleBaselineAgent(),
        "Proposed Support Agent": SupportAgentPipeline()
    }

    use_api = "--use-api" in sys.argv
    judge = LLMJudgeRubric(use_api=use_api)
    summary_results = []
    detailed_metrics = {}

    y_true_intent = [d["true_intent"] for d in dataset]
    y_true_escalation = [d["true_escalation"] for d in dataset]
    references = [d["reference_reply"] for d in dataset]

    for name, model in models.items():
        logger.info(f"Evaluating {name}...")
        y_pred_intent = []
        y_pred_esc = []
        pred_replies = []
        latencies = []
        judge_scores = {
            "groundedness": [],
            "helpfulness": [],
            "tone_safety": [],
            "escalation": [],
            "overall": []
        }

        for sample in dataset:
            res = model.process(sample["text"])
            
            y_pred_intent.append(res["intent"])
            y_pred_esc.append(res["escalation"]["should_escalate"])
            pred_replies.append(res["draft_reply"])
            latencies.append(res.get("latency_ms", 1.5))

            # Run LLM-as-a-Judge
            j_res = judge.evaluate_reply(
                customer_text=sample["text"],
                predicted_reply=res["draft_reply"],
                predicted_intent=res["intent"],
                predicted_escalation=res["escalation"]["should_escalate"],
                true_intent=sample["true_intent"],
                true_escalation=sample["true_escalation"],
                reference_reply=sample["reference_reply"]
            )
            judge_scores["groundedness"].append(j_res["groundedness"])
            judge_scores["helpfulness"].append(j_res["helpfulness"])
            judge_scores["tone_safety"].append(j_res["tone_safety"])
            judge_scores["escalation"].append(j_res["escalation_appropriateness"])
            judge_scores["overall"].append(j_res["overall_score"])

        intent_metrics = AutomatedMetricsEvaluator.evaluate_intent_classification(y_true_intent, y_pred_intent)
        esc_metrics = AutomatedMetricsEvaluator.evaluate_escalation(y_true_escalation, y_pred_esc)
        lex_metrics = AutomatedMetricsEvaluator.compute_lexical_similarity(pred_replies, references)

        row = {
            "Model": name,
            "Intent Acc": f"{intent_metrics['accuracy']*100:.1f}%",
            "Intent Macro-F1": f"{intent_metrics['macro_f1']:.3f}",
            "Escalation F1": f"{esc_metrics['escalation_f1']:.3f}",
            "Escalation Recall": f"{esc_metrics['escalation_recall']*100:.1f}%",
            "Groundedness (1-5)": f"{sum(judge_scores['groundedness'])/len(judge_scores['groundedness']):.2f}",
            "Judge Overall (1-5)": f"{sum(judge_scores['overall'])/len(judge_scores['overall']):.2f}",
            "Avg Latency (ms)": f"{sum(latencies)/len(latencies):.1f}ms"
        }
        summary_results.append(row)
        detailed_metrics[name] = {
            "intent": intent_metrics,
            "escalation": esc_metrics,
            "lexical": lex_metrics,
            "judge_means": {k: round(sum(v)/len(v), 3) for k, v in judge_scores.items()}
        }

    # Print Table
    print("\n" + "="*88)
    print("                HIVER AI SUPPORT AGENT — BENCHMARK EVALUATION RESULTS")
    print("="*88)
    print(format_table(summary_results))
    print("="*88)

    # Save artifacts
    out_dir = Path("reports/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "benchmark_summary.json").write_text(json.dumps(detailed_metrics, indent=2), encoding="utf-8")
    logger.info(f"Benchmark artifacts saved to {out_dir}")

if __name__ == "__main__":
    run_benchmark()
