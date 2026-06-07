"""
Explainability Engine: generates human-readable explanation for each decision.
"""


def explain(
    label: str,
    hybrid_score: float,
    rule_score: float,
    ml_score: float,
    triggered_rules: list[dict],
    top_tokens: list[dict],
    action: str,
) -> dict:
    """Build a structured explanation object for the API response."""

    # Narrative summary
    if label == "malicious":
        summary = (
            f"This prompt was classified as MALICIOUS with a threat score of "
            f"{hybrid_score:.2f}. It triggered {len(triggered_rules)} security "
            f"rule(s) and the ML model assigned an adversarial probability of "
            f"{ml_score:.2f}. The request has been blocked."
        )
    elif label == "suspicious":
        summary = (
            f"This prompt was classified as SUSPICIOUS with a threat score of "
            f"{hybrid_score:.2f}. It shows partial adversarial signals — "
            f"{len(triggered_rules)} rule(s) triggered, ML adversarial probability: "
            f"{ml_score:.2f}. The prompt has been rewritten for safe processing."
        )
    else:
        summary = (
            f"This prompt appears BENIGN. Threat score: {hybrid_score:.2f}. "
            f"No security rules were triggered and the ML model assigned a low "
            f"adversarial probability of {ml_score:.2f}."
        )

    # Score breakdown
    score_breakdown = {
        "hybrid_score": hybrid_score,
        "rule_score": rule_score,
        "ml_score": ml_score,
        "rule_weight": 0.55,
        "ml_weight": 0.45,
        "formula": f"({rule_score:.3f} × 0.55) + ({ml_score:.3f} × 0.45) = {hybrid_score:.3f}",
    }

    # Rule findings
    rule_findings = [
        {
            "rule": r["name"].replace("_", " ").title(),
            "confidence": f"{r['weight']:.0%}",
            "detail": r["description"],
        }
        for r in triggered_rules
    ]

    # Top ML tokens
    ml_findings = [
        {
            "token": t["token"],
            "impact": round(t["weight"], 4),
        }
        for t in top_tokens
        if t["weight"] > 0
    ]

    # Action taken
    action_map = {
        "allow": "Prompt allowed — forwarded to the LLM.",
        "rewrite": "Prompt rewritten — injection phrases removed before forwarding.",
        "block": "Prompt blocked — request rejected, incident logged.",
    }

    return {
        "summary": summary,
        "score_breakdown": score_breakdown,
        "rule_findings": rule_findings,
        "ml_findings": ml_findings,
        "action_taken": action_map.get(action, action),
        "thresholds": {
            "benign": "< 0.30",
            "suspicious": "0.30 – 0.70",
            "malicious": "> 0.70",
        },
    }
