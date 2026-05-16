from typing import Any
from app.models import ChatResponse, Recommendation


def _build_url_map(catalog: list[dict]) -> dict[str, dict]:
    m = {}
    for item in catalog:
        url = item.get("url") or ""
        if url:
            m[url] = item
    return m


def sanitize_chat_response(resp: Any, catalog: list[dict]) -> ChatResponse:
    """Ensure the response conforms to ChatResponse schema and only references catalog items.

    - Coerce dict into ChatResponse where possible.
    - Replace any recommendations with canonical catalog entries when URLs match.
    - Enforce recommendations length <= 10 and end_of_conversation consistency.
    - Guarantee `reply` is non-empty.
    """
    url_map = _build_url_map(catalog)

    # Coerce to dict first
    data = {}
    if isinstance(resp, ChatResponse):
        data = resp.dict()
    elif isinstance(resp, dict):
        data = dict(resp)
    else:
        # Unknown type, produce a safe clarifying response
        return ChatResponse(
            reply="Could you share more about the role and seniority?",
            recommendations=[],
            end_of_conversation=False,
        )

    # Ensure reply
    reply = data.get("reply") or "Could you share more about the role and seniority?"

    # Normalize recommendations
    recs = []
    raw_recs = data.get("recommendations") or []
    if isinstance(raw_recs, list):
        for r in raw_recs[:10]:
            if not isinstance(r, dict):
                continue
            url = r.get("url")
            # Prefer canonical catalog entry when URL matches
            if url and url in url_map:
                item = url_map[url]
                recs.append(
                    Recommendation(
                        name=item.get("name", ""),
                        url=item.get("url", ""),
                        test_type=item.get("test_type", ""),
                    )
                )
            else:
                # skip non-catalog urls
                continue

    # If no recommendations, ensure empty list
    if not recs:
        recs = []

    # end_of_conversation should be true iff we have recommendations
    end_flag = bool(recs)

    return ChatResponse(reply=reply, recommendations=recs, end_of_conversation=end_flag)
