from src.evaluation.automated_metrics import AutomatedMetricsEvaluator
from src.evaluation.llm_judge import LLMJudgeRubric

def test_automated_metrics():
    y_true = ["ORDER_STATUS_DELIVERY", "REFUND_AND_RETURNS"]
    y_pred = ["ORDER_STATUS_DELIVERY", "REFUND_AND_RETURNS"]
    metrics = AutomatedMetricsEvaluator.evaluate_intent_classification(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0

def test_llm_judge():
    judge = LLMJudgeRubric()
    score = judge.evaluate_reply(
        customer_text="Where is my order TBA9182?",
        predicted_reply="Track your order at amazon.com/your-orders!",
        predicted_intent="ORDER_STATUS_DELIVERY",
        predicted_escalation=False,
        true_intent="ORDER_STATUS_DELIVERY",
        true_escalation=False,
        reference_reply="Track at amazon.com/your-orders."
    )
    assert score["overall_score"] >= 4.0
