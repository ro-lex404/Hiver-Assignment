import re
import math
from collections import Counter
from typing import Dict, Any, List, Tuple
from src.intent.taxonomy import INTENT_TAXONOMY, ALL_INTENTS, DEFAULT_INTENT
from src.utils import clean_tweet_text, logger

class IntentClassifier:
    """
    Hybrid Lexical + Semantic TF-IDF Intent Classifier.
    Runs with zero external C-dependencies or scikit-learn for maximum portability,
    while offering high-precision intent classification & confidence estimation.
    """

    def __init__(self):
        self._build_intent_exemplars()
        self._compute_tfidf_centroids()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        stop_words = {"the", "a", "an", "is", "are", "and", "or", "to", "for", "in", "on", "at", "my", "your", "it", "with", "this", "that"}
        return [w for w in words if w not in stop_words]

    def _build_intent_exemplars(self):
        self.doc_tokens = {}
        self.df_counts = Counter()
        for intent, data in INTENT_TAXONOMY.items():
            tokens = self._tokenize(f"{data['description']} {' '.join(data['keywords'])} {data['policy']}")
            self.doc_tokens[intent] = Counter(tokens)
            for unique_t in set(tokens):
                self.df_counts[unique_t] += 1
        self.num_classes = len(INTENT_TAXONOMY)

    def _compute_tfidf_centroids(self):
        self.intent_vectors = {}
        for intent, counts in self.doc_tokens.items():
            vec = {}
            total = sum(counts.values())
            for word, freq in counts.items():
                tf = freq / max(total, 1)
                idf = math.log(1 + (self.num_classes / max(1, self.df_counts[word])))
                vec[word] = tf * idf
            # normalize
            norm = math.sqrt(sum(v*v for v in vec.values()))
            self.intent_vectors[intent] = {w: v / max(norm, 1e-6) for w, v in vec.items()}

    def _cosine_similarity(self, query_vec: Dict[str, float], doc_vec: Dict[str, float]) -> float:
        dot = sum(query_vec.get(w, 0.0) * doc_vec[w] for w in doc_vec if w in query_vec)
        return float(dot)

    def predict(self, text: str) -> Dict[str, Any]:
        clean_text = clean_tweet_text(text).lower()
        if not clean_text:
            return {
                "intent": DEFAULT_INTENT,
                "confidence": 0.50,
                "top_candidates": [(DEFAULT_INTENT, 0.50)],
                "method": "fallback_empty"
            }

        q_tokens = self._tokenize(clean_text)
        q_counts = Counter(q_tokens)
        q_total = sum(q_counts.values())
        
        q_vec = {}
        for word, freq in q_counts.items():
            tf = freq / max(q_total, 1)
            idf = math.log(1 + (self.num_classes / max(1, self.df_counts.get(word, 0) + 1)))
            q_vec[word] = tf * idf
        
        q_norm = math.sqrt(sum(v*v for v in q_vec.values()))
        if q_norm > 0:
            q_vec = {w: v / q_norm for w, v in q_vec.items()}

        # Calculate keyword match bonus
        keyword_scores = {intent: 0 for intent in ALL_INTENTS}
        for intent, data in INTENT_TAXONOMY.items():
            for kw in data["keywords"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', clean_text):
                    keyword_scores[intent] += 1

        candidates: List[Tuple[str, float]] = []
        for intent in ALL_INTENTS:
            sim = self._cosine_similarity(q_vec, self.intent_vectors[intent])
            kw_bonus = min(keyword_scores[intent] * 0.15, 0.35)
            blended = sim * 0.65 + kw_bonus
            candidates.append((intent, float(blended)))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_intent, top_score = candidates[0]
        confidence = min(max(top_score * 1.5 + (0.20 if keyword_scores[top_intent] > 0 else 0.0), 0.40), 0.98)

        return {
            "intent": top_intent,
            "confidence": round(confidence, 3),
            "top_candidates": [(c[0], round(c[1], 3)) for c in candidates[:3]],
            "method": "hybrid_lexical_semantic"
        }
