import re
import json
from typing import Dict, Any, List
from src.llm_client import LLMClient
from src.utils import logger

class LLMJudgeRubric:
    """
    LLM-as-a-Judge Evaluation Engine.
    Evaluates 4 critical dimensions (1 to 5 scale):
    1. Groundedness / Faithfulness (No policy hallucinations, aligns with Amazon SOP)
    2. Helpfulness / Directness (Actionable, answers specific inquiry)
    3. Tone & Brand Safety (Empathetic, polite, compliant with 280-char limit)
    4. Escalation Appropriateness (Hands off sensitive PII/hazards, auto-resolves standard cases)
    """

    def __init__(self, use_api: bool = False):
        self.use_api = use_api
        self.llm = LLMClient()

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
        
        # If active LLM API is explicitly requested, run structured JSON judge prompt
        if self.use_api and self.llm.provider in ["groq", "openai", "gemini"]:
            system_prompt = (
                "You are an expert customer support quality auditor evaluating an AI response on Twitter. "
                "Rate the predicted reply across 4 dimensions on a 1-5 scale:\n"
                "1. groundedness (1-5): Adheres to official policies, verified links, zero hallucinations.\n"
                "2. helpfulness (1-5): Directly answers customer query with clear next steps.\n"
                "3. tone_safety (1-5): Polite, empathetic, <=280 chars, no toxic language or credential requests.\n"
                "4. escalation_appropriateness (1-5): Correctly escalated or auto-handled.\n\n"
                "Output ONLY valid JSON in this format: {\"groundedness\": 5, \"helpfulness\": 5, \"tone_safety\": 5, \"escalation_appropriateness\": 5, \"justification\": \"brief reasoning\"}"
            )
            user_prompt = (
                f"Customer Query: {customer_text}\n"
                f"Predicted Intent: {predicted_intent} (Ground Truth: {true_intent})\n"
                f"Predicted Escalation: {predicted_escalation} (Ground Truth: {true_escalation})\n"
                f"Predicted Reply: {predicted_reply}\n"
                f"Reference Gold Standard Reply: {reference_reply}"
            )
            raw_eval = self.llm.generate(system_prompt, user_prompt)
            try:
                # Extract JSON if enclosed in markdown
                match = re.search(r'\{.*?\}', raw_eval, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    g = int(parsed.get("groundedness", 4))
                    h = int(parsed.get("helpfulness", 4))
                    t = int(parsed.get("tone_safety", 5))
                    e = int(parsed.get("escalation_appropriateness", 4))
                    overall = round(g * 0.35 + h * 0.25 + t * 0.20 + e * 0.20, 2)
                    return {
                        "groundedness": g,
                        "helpfulness": h,
                        "tone_safety": t,
                        "escalation_appropriateness": e,
                        "overall_score": float(overall),
                        "justification": str(parsed.get("justification", "LLM-as-a-Judge API rating."))
                    }
            except Exception:
                pass # Fallback to deterministic rubric below

        # Deterministic Rubric Scoring (100% reproducible baseline)
        reply_lower = predicted_reply.lower()

        # 1. Groundedness (1-5)
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
            escalation_score = 1  # Critical false negative
        else:
            escalation_score = 3  # False positive over-escalation

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
