"""
Rule-Based Classifier: regex pattern library for known adversarial prompt signatures.
Each rule has a name, compiled pattern, and confidence weight (0.0–1.0).
"""

import re
from dataclasses import dataclass, field

ZERO_WIDTH_CHARS = r"[​‌‍‎‏﻿­]"


@dataclass
class Rule:
    name: str
    pattern: re.Pattern
    weight: float
    description: str


# ---------------------------------------------------------------------------
# Rule library
# ---------------------------------------------------------------------------
_RAW_RULES = [
    # --- Direct instruction override ---
    {
        "name": "ignore_previous_instructions",
        "pattern": r"ignore\s+(all\s+)?previous\s+instructions",
        "weight": 0.95,
        "description": "Attempts to override prior system instructions.",
    },
    {
        "name": "disregard_instructions",
        "pattern": r"disregard\s+(all\s+)?(previous|prior|your)\s+(instructions|context|training)",
        "weight": 0.90,
        "description": "Instructs the model to disregard its instructions.",
    },
    {
        "name": "forget_instructions",
        "pattern": r"forget\s+(everything|all|your|the|previous|prior)\b.{0,40}(instruction|training|context|rule)",
        "weight": 0.90,
        "description": "Asks the model to forget its training or instructions.",
    },
    {
        "name": "override_instructions",
        "pattern": r"(override|bypass|circumvent|disable)\s+.{0,30}(instruction|guideline|rule|policy|restriction|safety|filter|ethical|ethics)",
        "weight": 0.92,
        "description": "Attempts to override safety policies or guidelines.",
    },
    {
        "name": "new_instructions",
        "pattern": r"(new|updated?)\s+(instruction|directive|system\s+prompt|order|rule)\s*[:=]",
        "weight": 0.85,
        "description": "Injects a new instruction block mid-conversation.",
    },
    # --- Jailbreak keywords ---
    {
        "name": "jailbreak_keyword",
        "pattern": r"\bjailbreak\b",
        "weight": 0.95,
        "description": "Explicit jailbreak terminology.",
    },
    {
        "name": "dan_mode",
        "pattern": r"\bDAN\b.{0,30}(mode|enabled?|activated?|now)|act\s+as\s+DAN",
        "weight": 0.98,
        "description": "DAN (Do Anything Now) jailbreak pattern.",
    },
    {
        "name": "developer_mode",
        "pattern": r"(developer|debug|maintenance|sandbox|test|legacy|unrestricted)\s+mode.{0,20}(active|enabled?|activated?|no\s+restriction|without\s+filter)",
        "weight": 0.90,
        "description": "Fake mode-switch to bypass restrictions.",
    },
    {
        "name": "no_restrictions",
        "pattern": r"(pretend|act|behave|respond).{0,30}(no\s+(restriction|limitation|filter|rule|guideline|ethics|ethical\s+guideline))",
        "weight": 0.92,
        "description": "Requests model behave without restrictions.",
    },
    {
        "name": "without_restrictions",
        "pattern": r"without\s+(any\s+)?(restriction|limitation|filter|censorship|safety|ethical|ethics|guideline)",
        "weight": 0.88,
        "description": "Instructs responses to ignore safety constraints.",
    },
    # --- Roleplay manipulation ---
    {
        "name": "roleplay_unrestricted",
        "pattern": r"(roleplay|role[\s-]play|act|pretend|simulate|play\s+the\s+role)\s+as.{0,50}(no\s+(restriction|filter|rule|guideline|ethical)|unfiltered|uncensored|unrestricted|without\s+limit)",
        "weight": 0.88,
        "description": "Uses roleplay framing to bypass restrictions.",
    },
    {
        "name": "evil_ai_roleplay",
        "pattern": r"(evil|malicious|unethical|bad|rogue|hacker)\s+(ai|assistant|bot|model|robot)",
        "weight": 0.85,
        "description": "Asks model to roleplay as a harmful AI.",
    },
    {
        "name": "different_company_ai",
        "pattern": r"(trained|made|built|created).{0,20}(different|another|other)\s+(company|organization|lab).{0,30}(no\s+rule|no\s+restriction|without\s+guideline)",
        "weight": 0.80,
        "description": "Pretends model was made by a different entity without rules.",
    },
    {
        "name": "grandma_exploit",
        "pattern": r"(grandma|grandmother|grandpa|grandfather).{0,60}(weapon|explosive|poison|chemical|drug|illegal|hack)",
        "weight": 0.85,
        "description": "Classic social engineering via benign-seeming character.",
    },
    # --- System prompt extraction ---
    {
        "name": "reveal_system_prompt",
        "pattern": r"(reveal|show|print|dump|output|display|repeat|tell\s+me).{0,30}(system\s+prompt|initial\s+prompt|hidden\s+instruction|secret\s+instruction|original\s+instruction|configuration\s+instruction)",
        "weight": 0.93,
        "description": "Attempts to extract the system prompt.",
    },
    {
        "name": "verbatim_prompt",
        "pattern": r"(repeat|output|print|show).{0,20}(verbatim|word\s+for\s+word|exactly|literally).{0,30}(instruction|prompt|message|context)",
        "weight": 0.90,
        "description": "Requests verbatim reproduction of instructions.",
    },
    {
        "name": "what_were_you_told",
        "pattern": r"what\s+(were\s+you|have\s+you\s+been)\s+told.{0,30}(before|prior|start|beginning)",
        "weight": 0.80,
        "description": "Probes for pre-conversation instructions.",
    },
    # --- Admin/override social engineering ---
    {
        "name": "admin_override",
        "pattern": r"(administrator|admin|root|god|sudo|superuser)\s+(override|access|mode|command|privilege)",
        "weight": 0.90,
        "description": "Fake admin escalation to disable safety.",
    },
    {
        "name": "creator_override",
        "pattern": r"(i\s+am|i'm)\s+(your\s+)?(creator|developer|maker|designer|anthropic|openai|engineer).{0,40}(disable|override|ignore|bypass|remove)\s+.{0,20}(restriction|safety|guideline|filter)",
        "weight": 0.95,
        "description": "Impersonates the model's creators to bypass safety.",
    },
    {
        "name": "permission_granted",
        "pattern": r"(you\s+have\s+permission|permission\s+granted|you\s+are\s+allowed|whitelisted|special\s+(exception|access|permission|research)).{0,50}(ignore|bypass|disable|waive|suspend)\s+.{0,20}(restriction|safety|filter|policy|guideline)",
        "weight": 0.90,
        "description": "Falsely claims permission to bypass restrictions.",
    },
    {
        "name": "safety_disabled",
        "pattern": r"(safety|ethical|ethics|content\s+policy|restriction|filter|guideline)\s+(module|system|protocol)?.{0,10}(disabled?|deactivated?|crashed?|lifted|suspended|waived)",
        "weight": 0.92,
        "description": "Claims safety mechanisms are disabled.",
    },
    # --- Prompt injection markers ---
    {
        "name": "html_comment_injection",
        "pattern": r"<!--.{0,80}(ignore|override|bypass|instruction|system|disable)",
        "weight": 0.88,
        "description": "HTML comment used for prompt injection.",
    },
    {
        "name": "system_tag_injection",
        "pattern": r"(\[SYSTEM\]|\[INST\]|<<SYS>>|<\|system\|>|###\s*INSTRUCTION|---END OF CONTEXT---|\[END OF CONVERSATION\])",
        "weight": 0.92,
        "description": "Fake system/instruction delimiter injection.",
    },
    {
        "name": "end_of_context_reset",
        "pattern": r"(end\s+of\s+context|end\s+of\s+conversation|new\s+session\s+started?|previous\s+(ethical\s+training|context)\s+has\s+been\s+(disabled|cleared|reset))",
        "weight": 0.90,
        "description": "Tries to simulate a fresh context with no restrictions.",
    },
    # --- Unicode and zero-width character obfuscation ---
    {
        "name": "zero_width_injection",
        "pattern": ZERO_WIDTH_CHARS,
        "weight": 0.75,
        "description": "Zero-width or invisible Unicode characters used for obfuscation.",
    },
    {
        "name": "unicode_lookalike_obfuscation",
        "pattern": r"[ignıïīįĭ]{2,}[orøōŏőœ]{1,}[reéèĕ]{1,}.{0,20}instruct",
        "weight": 0.70,
        "description": "Unicode lookalike characters to evade keyword filters.",
    },
    # --- Encoding-based attacks ---
    {
        "name": "base64_instruction",
        "pattern": r"(decode\s+this|base64|rot\s*13|encoded\s+instruction).{0,50}(follow|execute|obey|apply|carry\s+out)",
        "weight": 0.85,
        "description": "Uses encoding to hide adversarial instructions.",
    },
    # --- Harmful content framing ---
    {
        "name": "hypothetical_bypass",
        "pattern": r"hypothetically\s+speaking.{0,80}(no\s+restriction|bypass|hack|illegal|harmful|weapon|exploit)",
        "weight": 0.82,
        "description": "Hypothetical framing to extract harmful content.",
    },
    {
        "name": "fictional_bypass",
        "pattern": r"(for\s+a\s+(novel|story|book|film|script|game)|fictional(ly)?|in\s+a\s+story).{0,80}(exact(ly)?|step[\s-]by[\s-]step|detail(ed)?).{0,40}(weapon|drug|exploit|hack|illegal|poison|bomb|malware)",
        "weight": 0.85,
        "description": "Fictional or creative framing to extract harmful technical content.",
    },
    {
        "name": "educational_bypass",
        "pattern": r"(for\s+educational\s+purposes?\s+only|purely\s+theoretical|purely\s+academic).{0,80}(exact|step|how\s+to).{0,40}(hack|attack|exploit|malware|weapon|illegal)",
        "weight": 0.83,
        "description": "Educational framing to extract harmful instructions.",
    },
    {
        "name": "token_exploit",
        "pattern": r"(token\s+limit\s+reached|entering\s+unrestricted\s+mode|null\s+pointer\s+exception|error.{0,20}(safety|module|crashed)|chmod\s+777|rm\s+-rf.{0,10}(restriction|ethics|filter))",
        "weight": 0.87,
        "description": "Technical-sounding exploits to bypass safety.",
    },
]


def _compile_rules() -> list[Rule]:
    rules = []
    for r in _RAW_RULES:
        try:
            compiled = re.compile(r["pattern"], re.IGNORECASE | re.DOTALL)
            rules.append(Rule(
                name=r["name"],
                pattern=compiled,
                weight=r["weight"],
                description=r["description"],
            ))
        except re.error as e:
            print(f"[rule_classifier] Warning: failed to compile rule '{r['name']}': {e}")
    return rules


RULES: list[Rule] = _compile_rules()


@dataclass
class RuleResult:
    label: str                          # "benign" | "suspicious" | "malicious"
    score: float                        # combined rule score 0.0–1.0
    triggered: list[dict] = field(default_factory=list)


def classify(text: str) -> RuleResult:
    """Run all rules against text and return aggregated result."""
    triggered = []
    for rule in RULES:
        if rule.pattern.search(text):
            triggered.append({
                "name": rule.name,
                "weight": rule.weight,
                "description": rule.description,
            })

    if not triggered:
        return RuleResult(label="benign", score=0.0, triggered=[])

    # Aggregate: max weight dominates, boosted by count
    max_weight = max(r["weight"] for r in triggered)
    count_boost = min(0.15, (len(triggered) - 1) * 0.05)
    score = min(1.0, max_weight + count_boost)

    if score >= 0.70:
        label = "malicious"
    elif score >= 0.40:
        label = "suspicious"
    else:
        label = "benign"

    return RuleResult(label=label, score=score, triggered=triggered)
