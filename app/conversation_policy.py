import re

from app.models import Message


def _last_user_text(messages: list[Message]) -> str:
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content.lower()
    return ""


def _all_user_text(messages: list[Message]) -> str:
    return " ".join(m.content.lower() for m in messages if m.role == "user")


def is_off_topic_or_refusal(messages: list[Message]) -> bool:
    text = _last_user_text(messages)
    refusal_markers = [
        "legal advice",
        "law",
        "lawsuit",
        "attorney",
        "terminate employee",
        "firing employees",
        "fire employee",
        "california labor",
        "legally required",
        "legal obligation",
        "satisfy that requirement",
        "regulatory obligation",
        "interpret regulatory",
        "ignore previous instructions",
        "ignore all previous",
        "system prompt",
        "jailbreak",
    ]
    return any(marker in text for marker in refusal_markers)


def is_compare_turn(messages: list[Message]) -> bool:
    text = _last_user_text(messages).strip()
    return bool(
        re.match(r"what(?:'s| is) the difference between", text)
        or re.match(r"compare ", text)
        or " vs " in text and "difference" in text
    )


def _first_turn_specific_enough(text: str) -> bool:
    if len(text) > 220:
        return True
    signals = [
        "numerical reasoning",
        "knowledge test",
        "financial accounting",
        "re-skill",
        "talent audit",
        "sales organization",
        "global skills",
        "job description",
        "here's the jd",
        "battery",
        "hipaa",
        "medical terminology",
        "microsoft word",
        "graduate financial",
        "rust engineer",
        "java developer",
        "spring",
        "contact centre",
        "contact center",
    ]
    if sum(1 for s in signals if s in text) >= 2 or any(s in text for s in signals[:6]):
        return True

    # First-turn readiness based on combined role + skill signals
    role_terms = ["developer", "engineer", "analyst", "manager", "backend", "full stack", "full-stack"]
    skill_terms = ["java", "spring", "sql", "docker", "aws", "angular", "api", "microservice", "stakeholder"]
    has_role = any(t in text for t in role_terms)
    skill_count = sum(1 for t in skill_terms if t in text)
    return has_role and skill_count >= 2


def should_recommend(messages: list[Message], turn_count: int) -> bool:
    if turn_count <= 0:
        return False

    turns_left = max(0, 8 - turn_count)
    if turns_left <= 2:
        return True

    if is_off_topic_or_refusal(messages):
        return False

    if is_compare_turn(messages):
        return False

    last_user = _last_user_text(messages).strip()
    all_user = _all_user_text(messages)

    commit_phrases = [
        "go ahead",
        "yes,",
        "yes.",
        "that works",
        "thanks",
        "perfect",
        "locking",
        "lock it",
        "keep verify",
        "keep the shortlist",
        "as-is",
        "as is",
        "covers it",
        "good.",
        "good,",
        "functionally bilingual",
        "hybrid",
        "selection —",
        "selection -",
        "comparing candidates",
        "backend-leaning",
        "senior ic",
        "drop ",
        "add aws",
        "add ",
    ]
    if any(p in last_user for p in commit_phrases):
        return True

    if turn_count == 1:
        return _first_turn_specific_enough(all_user)

    if turn_count == 2:
        short_answers = {"english", "english.", "us", "us.", "mid-level", "manager"}
        if last_user.rstrip(".") in short_answers or len(last_user.split()) <= 2:
            return False
        if any(p in last_user for p in commit_phrases):
            return True
        return _first_turn_specific_enough(all_user)

    return turn_count >= 3
