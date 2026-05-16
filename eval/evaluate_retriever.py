import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.retriever import CatalogRetriever


def calculate_recall_at_k(retrieved, expected_names):
    from app.name_match import names_match

    if not expected_names:
        return 1.0

    actual_names = [item.get("name", "") for item in retrieved]
    hits = 0
    for expected in expected_names:
        if any(names_match(expected, act) for act in actual_names):
            hits += 1
    return hits / len(expected_names)


def load_trace(filepath):
    with open(filepath, "r", encoding="utf-8") as handle:
        content = handle.read()

    messages = []
    expected_names = []

    turns = re.split(r"### Turn \d+", content)[1:]
    for turn in turns:
        user_match = re.search(r"\*\*User\*\*\s*>\s*(.*?)(?=\*\*Agent\*\*|$)", turn, re.DOTALL)
        if user_match:
            messages.append(user_match.group(1).strip())

        for line in turn.split("\n"):
            line = line.strip()
            if line.startswith("|") and not line.startswith("| # |") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3 and parts[2]:
                    if parts[2] not in expected_names:
                        expected_names.append(parts[2])

    return messages, expected_names


def build_queries(messages: list[str]) -> list[str]:
    from app.query_builder import build_queries as _build

    wrapped = [{"role": "user", "content": m} for m in messages]
    return _build(wrapped)


def run_evaluation():
    print("Starting retriever-only evaluation...", flush=True)
    catalog_path = os.path.join(ROOT_DIR, "data", "catalog.json")
    index_path = os.path.join(ROOT_DIR, "data", "catalog.index")
    retriever = CatalogRetriever(catalog_path, index_path)
    traces_dir = os.path.join(os.path.dirname(__file__), "traces")

    total_recall = 0.0
    trace_count = 0

    for filename in sorted(os.listdir(traces_dir)):
        if not filename.endswith(".md"):
            continue

        messages, expected_names = load_trace(os.path.join(traces_dir, filename))
        queries = build_queries(messages)
        retrieved = retriever.search_multi(queries, top_k=10, candidate_k=120)
        recall = calculate_recall_at_k(retrieved, expected_names)

        total_recall += recall
        trace_count += 1

        print(f"{filename}: expected={len(expected_names)} retrieved={len(retrieved)} recall={recall:.2f}", flush=True)

    if trace_count:
        print("\n=============================", flush=True)
        print(f"RETRIEVER MEAN RECALL@10: {total_recall / trace_count:.2f}", flush=True)
        print("=============================", flush=True)


if __name__ == "__main__":
    run_evaluation()
