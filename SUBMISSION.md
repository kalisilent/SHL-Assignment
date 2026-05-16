Submission summary

- Evaluation results
  - Retriever-only: RETRIEVER MEAN RECALL@10 = 1.00
  - End-to-end (HTTP /chat): FINAL MEAN RECALL@10 = 1.00

- Robustness notes
  - Perturbation tests show some traces are fragile to short/generic last-turn queries and punctuation/typos (notably C1, C2, C7, C8, C9). See `scripts/perturb_eval.py` and `debug_perturb_out.txt` for details.

- Reproduction (run from repo root)

1) Install dependencies (use a venv):

```powershell
python -m pip install -r requirements.txt
```

2) Build or place FAISS index and catalog files in `data/` (already present in this workspace).

3) Retriever-only evaluation:

```powershell
python eval/evaluate_retriever.py
```

4) End-to-end evaluation (ensure the FastAPI app is running at http://127.0.0.1:8000):

```powershell
python eval/evaluate.py
```

5) Perturbation / paraphrase robustness test:

```powershell
python scripts/perturb_eval.py
# output written to debug_perturb_out.txt
```

- Quick configuration flags
  - Set `DISABLE_RETRIEVER_HEURISTICS=1` to ablate heuristic expansions/injections.

- Next recommended optional work
  - Add Unicode/punctuation normalization, broaden abbreviation map, and add small fuzzy-match tolerance (I can implement these if you want).
  - Consider a cross-encoder reranker for top-K candidates to improve robustness to paraphrases.

Files included for submission
- [eval/evaluate_retriever.py](eval/evaluate_retriever.py)
- [eval/evaluate.py](eval/evaluate.py)
- [scripts/perturb_eval.py](scripts/perturb_eval.py)
- [scripts/debug_retrieval.py](scripts/debug_retrieval.py)
- [app/retriever.py](app/retriever.py)

If you want, I can:
- create a zip of the repo for submission,
- commit these artifacts and open a pull request,
- or implement the short normalization patch now (Unicode/punctuation + query_builder fallback).

Tell me which of those (zip / commit+PR / normalization patch) to do next.