import asyncio
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.agent import Agent
from app.models import Message
from app.retriever import CatalogRetriever
from eval.evaluate_retriever import calculate_recall_at_k


def load_trace_full(filepath: str) -> tuple[list[dict], list[str]]:
    """Same message parsing as eval/evaluate.py (user + assistant turns)."""
    with open(filepath, encoding="utf-8") as handle:
        content = handle.read()

    messages: list[dict] = []
    expected_names: list[str] = []
    turns = re.split(r"### Turn \d+", content)[1:]
    for turn in turns:
        user_match = re.search(r"\*\*User\*\*\s*>\s*(.*?)(?=\*\*Agent\*\*|$)", turn, re.DOTALL)
        if user_match:
            messages.append({"role": "user", "content": user_match.group(1).strip()})
        agent_match = re.search(
            r"\*\*Agent\*\*\s*(.*?)(?=_No recommendations|_`end_of_conversation`|\| # \|)",
            turn,
            re.DOTALL,
        )
        if agent_match:
            messages.append({"role": "assistant", "content": agent_match.group(1).strip()})
        for line in turn.split("\n"):
            line = line.strip()
            if line.startswith("|") and not line.startswith("| # |") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3 and parts[2] and parts[2] not in expected_names:
                    expected_names.append(parts[2])

    if messages and messages[-1]["role"] == "assistant":
        messages.pop()
    return messages, expected_names


async def main() -> None:
    retriever = CatalogRetriever(
        os.path.join(ROOT, "data", "catalog.json"),
        os.path.join(ROOT, "data", "catalog.index"),
    )
    agent = Agent(retriever)
    traces_dir = os.path.join(ROOT, "eval", "traces")
    total = 0.0
    count = 0

    for filename in sorted(os.listdir(traces_dir)):
        if not filename.endswith(".md"):
            continue
        messages, expected = load_trace_full(os.path.join(traces_dir, filename))
        pydantic_messages = [Message(**m) for m in messages]
        turn_count = sum(1 for m in pydantic_messages if m.role == "user")
        response = await agent.respond(pydantic_messages, turn_count)
        recall = calculate_recall_at_k(
            [item.model_dump() for item in response.recommendations],
            expected,
        )
        total += recall
        count += 1
        print(f"{filename}: recall={recall:.2f} recs={len(response.recommendations)}")

    print(f"\nAGENT MEAN RECALL@10: {total / count:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
