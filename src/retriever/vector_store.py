import re
import math
from collections import Counter
from typing import List, Dict, Any
from src.utils import clean_tweet_text, logger

DEFAULT_HISTORICAL_RESOLUTIONS: List[Dict[str, str]] = [
    {
        "query": "Where is my package tracking TBA9821 delayed in transit?",
        "resolution": "We understand your concern! You can track your real-time delivery progress at amazon.com/your-orders. If not received within 24h of expected date, please let us know!",
        "intent": "ORDER_STATUS_DELIVERY"
    },
    {
        "query": "Package marked delivered on porch but nothing is there.",
        "resolution": "We apologize for the missing package. Please check with household members and around your porch. If still missing, send us a DM with order details so we can assist!",
        "intent": "ORDER_STATUS_DELIVERY"
    },
    {
        "query": "How do I return my item at Kohl's or Whole Foods and when will I get my refund?",
        "resolution": "Refunds to cards typically take 3-5 business days after return scan. You can generate a free drop-off QR code at amazon.com/returns!",
        "intent": "REFUND_AND_RETURNS"
    },
    {
        "query": "Refund amount is wrong, only got partial refund.",
        "resolution": "We apologize for the refund discrepancy. Please send us a private DM with your order number so our billing team can review and correct this.",
        "intent": "REFUND_AND_RETURNS"
    },
    {
        "query": "Received broken glass item crushed in box.",
        "resolution": "We are so sorry your item arrived damaged! Please visit amazon.com/returns to request an instant replacement without shipping broken glass back.",
        "intent": "DAMAGED_DEFECTIVE_ITEM"
    },
    {
        "query": "Account locked 2fa otp not sending to phone.",
        "resolution": "To regain account access, please visit the Two-Step Verification Recovery page at amazon.com/help or DM us to begin verification.",
        "intent": "ACCOUNT_ACCESS_SECURITY"
    },
    {
        "query": "Why was I charged 139 dollars for Prime renewal?",
        "resolution": "We apologize for the unexpected charge. You can manage or cancel Prime for a full refund at amazon.com/gp/primecentral if benefits were unused.",
        "intent": "BILLING_AND_PRIME"
    },
    {
        "query": "Fire TV stick is stuck in a boot loop restarting.",
        "resolution": "Try unplugging the power adapter for 60 seconds and plugging into a wall outlet. For more steps, check amazon.com/devicesupport.",
        "intent": "PRODUCT_TROUBLESHOOTING"
    },
    {
        "query": "Delivery driver Mike was awesome thank you!",
        "resolution": "Thank you so much for sharing! We love hearing about exceptional delivery experiences and will pass your praise to Mike's fulfillment team!",
        "intent": "FEEDBACK_AND_GENERAL"
    }
]

class HistoricalResolutionRetriever:
    """Self-contained Pure-Python Hybrid Retriever for Historical Resolutions."""

    def __init__(self, initial_data: List[Dict[str, str]] = None):
        self.data = initial_data or DEFAULT_HISTORICAL_RESOLUTIONS
        self._index_corpus()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

    def _index_corpus(self):
        self.doc_vectors = []
        self.df = Counter()
        self.tokenized_corpus = []

        for d in self.data:
            text = f"{d['query']} {d.get('intent', '')}"
            tokens = self._tokenize(text)
            self.tokenized_corpus.append(tokens)
            for t in set(tokens):
                self.df[t] += 1

        n_docs = max(len(self.data), 1)
        for tokens in self.tokenized_corpus:
            counts = Counter(tokens)
            vec = {}
            total = max(sum(counts.values()), 1)
            for t, c in counts.items():
                tf = c / total
                idf = math.log(1 + (n_docs / self.df[t]))
                vec[t] = tf * idf
            norm = math.sqrt(sum(v*v for v in vec.values()))
            self.doc_vectors.append({k: v / max(norm, 1e-6) for k, v in vec.items()})

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        clean_q = clean_tweet_text(query)
        if not clean_q or not self.data:
            return []

        q_tokens = self._tokenize(clean_q)
        q_counts = Counter(q_tokens)
        q_total = max(sum(q_counts.values()), 1)
        n_docs = max(len(self.data), 1)

        q_vec = {}
        for t, c in q_counts.items():
            tf = c / q_total
            idf = math.log(1 + (n_docs / self.df.get(t, 1)))
            q_vec[t] = tf * idf
        q_norm = math.sqrt(sum(v*v for v in q_vec.values()))
        if q_norm > 0:
            q_vec = {k: v / q_norm for k, v in q_vec.items()}

        scores = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            dot = sum(q_vec.get(t, 0.0) * doc_vec[t] for t in doc_vec if t in q_vec)
            scores.append((idx, float(dot)))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            results.append({
                "score": round(score, 3),
                "query": self.data[idx]["query"],
                "resolution": self.data[idx]["resolution"],
                "intent": self.data[idx].get("intent", "GENERAL")
            })
        return results
