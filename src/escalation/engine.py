import re
from typing import Dict, Any, List
from src.intent.taxonomy import INTENT_TAXONOMY
from src.utils import logger

class EscalationEngine:
    """
    Multi-Signal Escalation Decision Engine.
    Evaluates:
    1. Mandatory Security/Fraud Intent Triggers
    2. PII / Account Lookup Requirement Detection
    3. Sentiment & Anger / Legal / Physical Hazard Signals
    4. Repeat Contact & Unresolved Friction Flags
    5. Intent Confidence Thresholds
    """

    CRITICAL_INTENTS = {"ACCOUNT_ACCESS_SECURITY"}

    LEGAL_OR_HAZARD_KEYWORDS = [
        "police", "lawyer", "legal action", "sue", "court", "hazard", 
        "smoke", "fire", "exploded", "injured", "scalded", "poison", "hospital"
    ]

    REPEAT_CONTACT_KEYWORDS = [
        "already called", "3 times", "third time", "second time", "still waiting",
        "replacement unit arrived damaged", "multiple times", "no one responded", "2 weeks"
    ]

    PII_KEYWORDS = [
        "look into my account", "my account email", "order id", "check my order",
        "unauthorized charge", "stolen card", "locked out", "refund difference", "where is my money"
    ]

    FRUSTRATION_KEYWORDS = [
        "theft", "thieves", "scam", "unacceptable", "furious", "disgusting",
        "worst service", "horrible", "fraud", "stolen"
    ]

    def __init__(self, confidence_threshold: float = 0.70):
        self.confidence_threshold = confidence_threshold

    def evaluate(self, text: str, intent: str, confidence: float) -> Dict[str, Any]:
        text_lower = text.lower()
        signals: List[str] = []
        risk_score = 0.0

        # Signal 1: Intent Critical Check
        if intent in self.CRITICAL_INTENTS:
            signals.append("MANDATORY_SECURITY_INTENT")
            risk_score += 0.85

        # Signal 2: Legal / Severe Physical Hazard
        for kw in self.LEGAL_OR_HAZARD_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                signals.append(f"SEVERE_HAZARD_OR_LEGAL_SIGNAL: '{kw}'")
                risk_score += 0.90
                break

        # Signal 3: Repeat Contact / Chronic Friction
        for kw in self.REPEAT_CONTACT_KEYWORDS:
            if kw in text_lower:
                signals.append(f"REPEAT_CONTACT_FLAG: '{kw}'")
                risk_score += 0.75
                break

        # Signal 4: PII / Private Account Access Needed
        for kw in self.PII_KEYWORDS:
            if kw in text_lower:
                signals.append(f"PII_ACCOUNT_LOOKUP_TRIGGER: '{kw}'")
                risk_score += 0.70
                break

        # Signal 5: Customer Frustration / Rage
        for kw in self.FRUSTRATION_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                signals.append(f"HIGH_FRUSTRATION_SIGNAL: '{kw}'")
                risk_score += 0.60
                break

        # Signal 6: Low Intent Confidence Fallback
        if confidence < self.confidence_threshold:
            signals.append(f"LOW_CONFIDENCE_CLASSIFICATION ({confidence:.2f} < {self.confidence_threshold})")
            risk_score += 0.50

        # Decision synthesis
        should_escalate = risk_score >= 0.65 or len(signals) > 0 and (
            "MANDATORY_SECURITY_INTENT" in str(signals) or 
            "SEVERE_HAZARD" in str(signals) or 
            "REPEAT_CONTACT" in str(signals) or
            "PII_ACCOUNT" in str(signals)
        )

        # Formulate human-readable stated reason
        stated_reason = self._synthesize_reason(signals, intent, should_escalate)

        return {
            "should_escalate": bool(should_escalate),
            "routing_action": "ESCALATE_TO_HUMAN" if should_escalate else "AUTO_HANDLE",
            "risk_score": min(round(risk_score, 2), 1.0),
            "stated_reason": stated_reason,
            "signals_triggered": signals
        }

    def _synthesize_reason(self, signals: List[str], intent: str, should_escalate: bool) -> str:
        if not should_escalate:
            return "Standard query eligible for automated self-service resolution under brand SOP."

        if any("SEVERE_HAZARD" in s for s in signals):
            return "Critical physical safety hazard or legal dispute requiring immediate Executive Team intervention."
        if any("MANDATORY_SECURITY" in s for s in signals):
            return "Suspected account compromise or 2FA verification requiring secure Account Security specialist."
        if any("REPEAT_CONTACT" in s for s in signals):
            return "Repeated unresolved customer friction or recurring defect requiring supervisor review."
        if any("PII_ACCOUNT" in s for s in signals):
            return "Resolution requires private account-level order lookup and PII verification via secure DM."
        if any("HIGH_FRUSTRATION" in s for s in signals):
            return "Elevated customer frustration and financial dispute exceeding automated resolution limits."
        if any("LOW_CONFIDENCE" in s for s in signals):
            return "Ambiguous query with low intent classification confidence requiring human clarification."

        return "Escalated to human support agent per brand escalation policy."
