import os
import re
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.retriever import CatalogRetriever
from app.name_match import names_match
from app.query_builder import build_queries

TRACES_DIR = os.path.join(ROOT, "eval", "traces")

synonyms = {
    "hipaa": ["privacy law", "health privacy"],
    "medical terminology": ["medical vocab", "clinical terms"],
    "microsoft word": ["word processor assessment", "ms word"],
    "verify g": ["gplus", "verify g plus", "g+"],
    "aws": ["amazon cloud", "amazon web services"],
    "docker": ["container", "docker containers"],
    "spring": ["spring framework", "springboot"],
}

def perturb_query(q: str):
    variants = [q]
    qlow = q.lower()
    # synonym replacements
    for k, vals in synonyms.items():
        if k in qlow:
            for v in vals:
                variants.append(re.sub(re.escape(k), v, qlow, flags=re.IGNORECASE))
    # remove key tokens
    tokens = re.findall(r"[A-Za-z0-9+]+", q)
    if len(tokens) > 3:
        # drop the most specific token
        variants.append(" ".join(tokens[:-1]))
    # small typo: swap two letters in first long token
    for t in tokens:
        if len(t) > 5:
            t2 = list(t)
            t2[1], t2[2] = t2[2], t2[1]
            variants.append(qlow.replace(t, "".join(t2)))
            break
    return list(dict.fromkeys(variants))


def load_trace(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    turns = re.split(r"### Turn \d+", content)[1:]
    messages = []
    expected = []
    for turn in turns:
        user_match = re.search(r"\*\*User\*\*\s*>\s*(.*?)(?=\*\*Agent\*\*|$)", turn, re.DOTALL)
        if user_match:
            messages.append({"role": "user", "content": user_match.group(1).strip()})
        for line in turn.split('\n'):
            line = line.strip()
            if line.startswith('|') and not line.startswith('| # |') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[2]:
                    if parts[2] not in expected:
                        expected.append(parts[2])
    return messages, expected


def calculate_recall(retrieved, expected_names):
    if not expected_names:
        return 1.0
    actual = [r.get('name','') for r in retrieved]
    hits = 0
    for exp in expected_names:
        if any(names_match(exp, a) for a in actual):
            hits += 1
    return hits / len(expected_names)


def main():
    catalog_path = os.path.join(ROOT, 'data', 'catalog.json')
    index_path = os.path.join(ROOT, 'data', 'catalog.index')
    retriever = CatalogRetriever(catalog_path, index_path)
    out_path = os.path.join(ROOT, 'debug_perturb_out.txt')
    out_handle = open(out_path, 'w', encoding='utf-8')

    for filename in sorted(os.listdir(TRACES_DIR)):
        if not filename.endswith('.md'):
            continue
        path = os.path.join(TRACES_DIR, filename)
        messages, expected = load_trace(path)
        queries = build_queries(messages)
        base_query = queries[0] if queries else ''
        variants = perturb_query(base_query)
        out_handle.write(f"\n--- Trace: {filename}\n")
        out_handle.write(f"Base query: {base_query}\n")
        out_handle.write(f"Expected: {expected}\n")
        for v in variants:
            retrieved = retriever.search_multi([v], top_k=10, candidate_k=120)
            recall = calculate_recall(retrieved, expected)
            line = f"Variant: {v[:200]} -> Recall: {recall:.2f}\n"
            out_handle.write(line)
            print(line, end='')

    out_handle.close()
    print(f"Wrote results to {out_path}")

if __name__ == '__main__':
    main()
