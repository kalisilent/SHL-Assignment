import re


def build_queries(messages: list) -> list[str]:
    """Build multi-query list from conversation (user messages)."""
    user_msgs = []
    for m in messages:
        role = m.role if hasattr(m, "role") else m.get("role")
        content = m.content if hasattr(m, "content") else m.get("content")
        if role == "user":
            user_msgs.append(content)

    if not user_msgs:
        return []

    last = user_msgs[-1]
    last_three = " ".join(user_msgs[-3:])
    recent = user_msgs[-5:]

    tokens = re.findall(r"[A-Za-z0-9+]+", last_three)
    keywords = [t for t in tokens if len(t) > 2]
    keyword_query = " ".join(keywords)

    queries = [last, last_three]
    for msg in recent:
        if msg and msg not in queries:
            queries.append(msg)
    if keyword_query:
        queries.append(keyword_query)
    return queries
