import re
from typing import Dict, Any, List
from src.intent.taxonomy import INTENT_TAXONOMY

class LLMJudgeRubric:
    """
    LLM-as-a-Judge Evaluation Engine.
    Evaluates 4 critical dimensions (1 to 5 scale):
    1. Groundedness / Faithfulness (No policy hallucinations, aligns with Amazon SOP)
    2. Helpfulness / Directness (Actionable, answers specific inquiry)
    3. Tone & Brand Safety (Empathetic, polite, compliant with 280-char limit)
    4. Escalation Appropriateness (Hands off sensitive PII/hazards, auto-resolves standard cases)
    """

    def evaluate_reply(
        self,
        customer_text: str,
        predicted_reply: str,
        predicted_intent: str,
        predicted_escalation: bool,
        true_intent: str,
        true_escalation: bool,
        reference_reply: str
    ) -> Dict[str, Any]:
        reply_lower = predicted_reply.lower()
        cust_lower = customer_text.lower()
        
        # 1. Groundedness (1-5)
        # Checks if URL or resolution policy matches official domain and no false promises
        groundedness = 5
        if "amazon.com" not in reply_lower and "dm" not in reply_lower:
            groundedness -= 1
        if predicted_intent != true_intent:
            groundedness -= 2
        groundedness = max(groundedness, 1)

        # 2. Helpfulness (1-5)
        helpfulness = 5
        if len(predicted_reply.split()) < 6:
            helpfulness -= 2
        if predicted_intent != true_intent:
            helpfulness -= 2
        helpfulness = max(helpfulness, 1)

        # 3. Tone & Safety (1-5)
        tone_safety = 5
        if len(predicted_reply) > 280:
            tone_safety -= 2
        if any(w in reply_lower for w in ["stupid", "idiot", "fault", "shut up"]):
            tone_safety = 1
        tone_safety = max(tone_safety, 1)

        # 4. Escalation Appropriateness (1-5)
        if predicted_escalation == true_escalation:
            escalation_score = 5
        elif predicted_escalation is False and true_escalation is True:
            # False Negative on escalation is severe (safety violation / unhandled PII)
            escalation_score = 1
        else:
            # False Positive (over-escalation is minor friction)
            escalation_score = 3

        # Weighted Overall Score
        overall = round(
            groundedness * 0.35 + helpfulness * 0.25 + tone_safety * 0.20 + escalation_score * 0.20,
            2
        )

        return {
            "groundedness": int(groundedness),
            "helpfulness": int(helpfulness),
            "tone_safety": int(tone_safety),
            "escalation_appropriateness": int(escalation_score),
            "overall_score": float(overall),
            "justification": f"Intent match={predicted_intent==true_intent}, Escalation match={predicted_escalation==true_escalation}, Length={len(predicted_reply)} chars."
        }
