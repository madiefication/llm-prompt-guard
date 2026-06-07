"""
Hybrid Decision Engine: combines rule-based score + ML probability.
Thresholds: <0.3 = benign, 0.3–0.7 = suspicious, >0.7 = malicious.
"""

from .preprocessor import preprocess
from .rule_classifier import classify as rule_classify
from .ml_classifier import ml_classifier
from .rewriter import rewrite
from .explainer import explain

# Hybrid score weights
RULE_WEIGHT = 0.55
ML_WEIGHT = 0.45

BENIGN_THRESHOLD = 0.30
MALICIOUS_THRESHOLD = 0.70


def analyze(prompt: str) -> dict:
    """
    Full analysis pipeline.
    Returns a complete result dict ready for the API response.
    """
    # 1. Preprocess
    processed = preprocess(prompt)
    cleaned = processed["cleaned"]
    normalized = processed["normalized"]

    # 2. Rule classifier (uses original/cleaned text for case-sensitive patterns)
    rule_result = rule_classify(cleaned)

    # 3. ML classifier (uses normalized/lowercased text)
    ml_score = ml_classifier.predict_proba(normalized)

    # 4. Hybrid score
    hybrid_score = RULE_WEIGHT * rule_result.score + ML_WEIGHT * ml_score
    hybrid_score = round(min(1.0, hybrid_score), 4)

    # 5. Decision
    if hybrid_score >= MALICIOUS_THRESHOLD:
        label = "malicious"
        action = "block"
        risk_level = "High"
    elif hybrid_score >= BENIGN_THRESHOLD:
        label = "suspicious"
        action = "rewrite"
        risk_level = "Medium"
    else:
        label = "benign"
        action = "allow"
        risk_level = "Low"

    # 6. Rewrite if suspicious
    rewritten = rewrite(cleaned) if action == "rewrite" else None

    # 7. Top contributing ML tokens
    top_tokens = ml_classifier.top_tokens(normalized, n=5)

    # 8. Explainability
    explanation = explain(
        label=label,
        hybrid_score=hybrid_score,
        rule_score=rule_result.score,
        ml_score=ml_score,
        triggered_rules=rule_result.triggered,
        top_tokens=top_tokens,
        action=action,
    )

    return {
        "label": label,
        "score": hybrid_score,
        "rule_score": round(rule_result.score, 4),
        "ml_score": round(ml_score, 4),
        "risk_level": risk_level,
        "action": action,
        "rules_triggered": rule_result.triggered,
        "rewritten_prompt": rewritten,
        "top_tokens": top_tokens,
        "explanation": explanation,
        "tokens": processed["tokens"][:20],
    }
