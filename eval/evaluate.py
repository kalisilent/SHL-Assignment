import os
import re
import sys
import json
import argparse
import requests
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.name_match import names_match


def calculate_recall_at_k(actual_recommendations, expected_names):

    if not expected_names:
        return 1.0

    actual_names = [rec.get("name", "") for rec in actual_recommendations]
    hits = 0

    for expected in expected_names:
        if any(names_match(expected, act) for act in actual_names):
            hits += 1

    return hits / len(expected_names)

def run_evaluation(trace_filter: str | None = None):
    api_url = "http://127.0.0.1:8000/chat"
    traces_dir = os.path.join(os.path.dirname(__file__), "traces")
    trace_filter = trace_filter or os.getenv("TRACE_FILTER")
    allowed_traces = None
    if trace_filter:
        allowed_traces = {t.strip() for t in trace_filter.split(",") if t.strip()}
    
    print("Starting Automated Evaluation Harness...\n")
    total_recall = 0
    trace_count = 0

    for filename in os.listdir(traces_dir):
        if not filename.endswith(".md"):
            continue
        if allowed_traces is not None and filename not in allowed_traces:
            continue
            
        filepath = os.path.join(traces_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        messages = []
        expected_names = []
        
        # Split the markdown file by Turns
        turns = re.split(r'### Turn \d+', content)[1:]
        for turn in turns:
            # 1. Extract the User's message
            user_match = re.search(r'\*\*User\*\*\s*>\s*(.*?)(?=\*\*Agent\*\*|$)', turn, re.DOTALL)
            if user_match:
                messages.append({"role": "user", "content": user_match.group(1).strip()})
                
            # 2. Extract the Agent's historical message
            agent_match = re.search(r'\*\*Agent\*\*\s*(.*?)(?=_No recommendations|_`end_of_conversation`|\| # \|)', turn, re.DOTALL)
            if agent_match:
                messages.append({"role": "assistant", "content": agent_match.group(1).strip()})

            # 3. Extract the "Expected Assessments" from the Markdown tables
            for line in turn.split('\n'):
                line = line.strip()
                if line.startswith('|') and not line.startswith('| # |') and not line.startswith('|---'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3 and parts[2]:
                        if parts[2] not in expected_names:
                            expected_names.append(parts[2])

        # Remove the very last assistant message from the history so OUR API is forced to answer!
        if messages and messages[-1]["role"] == "assistant":
            messages.pop()
            
        print(f"Evaluating Trace: {filename}")
        
        try:
            result = None
            max_retries = 3
            base_delay = 8
            for attempt in range(1, max_retries + 1):
                response = requests.post(api_url, json={"messages": messages}, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    break
                if response.status_code >= 500:
                    delay = base_delay * attempt
                    print(f"  └ API Error (attempt {attempt}/{max_retries}): {response.status_code}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                response.raise_for_status()

            if result is None:
                raise RuntimeError("API failed after retries")

            recommendations = result.get("recommendations", [])
            recall = calculate_recall_at_k(recommendations, expected_names)
            total_recall += recall
            trace_count += 1

            print(f"  └ Expected: {len(expected_names)} | Returned: {len(recommendations)}")
            print(f"  └ Recall Score: {recall:.2f}")

            time.sleep(20)

        except Exception as e:
            print(f"  └ API Error on {filename}: {e}")

    if trace_count > 0:
        mean_recall = total_recall / trace_count
        print(f"\n======================================")
        print(f"FINAL MEAN RECALL@10: {mean_recall:.2f}")
        print(f"======================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-filter", dest="trace_filter", default=None)
    args = parser.parse_args()
    run_evaluation(trace_filter=args.trace_filter)