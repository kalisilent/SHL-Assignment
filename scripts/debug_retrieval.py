from app.retriever import CatalogRetriever
import os, re, json

ROOT = os.path.dirname(os.path.dirname(__file__))
RETRIEVER = CatalogRetriever(os.path.join(ROOT, 'data', 'catalog.json'), os.path.join(ROOT, 'data', 'catalog.index'))

TRACES = ['C3.md', 'C7.md', 'C9.md']
TRACE_DIR = os.path.join(ROOT, 'eval', 'traces')


def parse_trace(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    messages = []
    expected_names = []
    turns = re.split(r"### Turn \d+", content)[1:]
    for turn in turns:
        user_match = re.search(r"\*\*User\*\*\s*>\s*(.*?)(?=\*\*Agent\*\*|$)", turn, re.DOTALL)
        if user_match:
            messages.append({'role': 'user', 'content': user_match.group(1).strip()})
        agent_match = re.search(r"\*\*Agent\*\*\s*(.*?)(?=_No recommendations|_`end_of_conversation`|\| # \||$)", turn, re.DOTALL)
        if agent_match:
            messages.append({'role': 'assistant', 'content': agent_match.group(1).strip()})
        for line in turn.split('\n'):
            line = line.strip()
            if line.startswith('|') and not line.startswith('| # |') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[2]:
                    if parts[2] not in expected_names:
                        expected_names.append(parts[2])
    # Remove last assistant message if present (same as evaluate.py)
    if messages and messages[-1]['role'] == 'assistant':
        messages.pop()
    return messages, expected_names


def build_search_query(messages):
    user_msgs = [m['content'] for m in messages if m['role'] == 'user']
    search_window = 3
    return ' '.join(user_msgs[-search_window:])


def match_expected_in_catalog(expected, item):
    # Compare by substring-insensitive matching (like evaluate)
    en = expected.lower()
    name = item.get('name','').lower()
    return en in name or name in en


if __name__ == '__main__':
    for trace in TRACES:
        path = os.path.join(TRACE_DIR, trace)
        messages, expected = parse_trace(path)
        query = build_search_query(messages)
        print('\n--- Trace:', trace)
        print('Search query:', query)
        print('Expected items:', expected)
        retrieved = RETRIEVER.search(query, top_k=100, candidate_k=300)
        names = [it.get('name','') for it in retrieved]
        print('\nRetrieved top', len(names))
        for i, n in enumerate(names[:50], start=1):
            print(f"{i:02d}. {n}")
        print('\nChecking expected items:')
        for exp in expected:
            found = False
            for idx, item in enumerate(retrieved):
                if match_expected_in_catalog(exp, item):
                    print(f"Expected '{exp}' FOUND at rank {idx+1}: {item.get('name')} ({item.get('url')})")
                    found = True
                    break
            if not found:
                print(f"Expected '{exp}' NOT FOUND in retrieved candidates")
