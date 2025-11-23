# LoCoMo SOTA v4.64 — Long‑Term Memory at SOTA Level

[![Reproducible](https://img.shields.io/badge/reproducible-yes-brightgreen)](#)
[![SOTA](https://img.shields.io/badge/SOTA-LoCoMo%20(Generous)-blueviolet)](#)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED)](#)

Long‑term memory for agents and RAG, built “in the wild”. The system achieves SOTA‑level results on LoCoMo (official generous judge), developed over ~10 months from scratch with the help of AI tools.

— Author: Viktor  
— Contact: Vkuz02452@gmail.com, ViktorAdamCore@pm.me  
— Mode: Reproducible out‑of‑the‑box (bundled DBs and FAISS indexes)

## Key Facts

- SOTA on LoCoMo (generous judge, GPT‑4o‑mini), 10 seeds × 10 conv.  
- Average accuracy (Generous): ~79.92% across all runs (100 total).  
- Strengths: commonsense (Cat4 ~87.78%), single‑hop factual (Cat1 ~82.92%).  
- Open architecture using well‑known blocks (FAISS, BM25, Cross‑Encoder) + custom MCA gate.  
  Exact top‑k, thresholds and private weights are intentionally not disclosed.  
- Full reproducibility: per‑conv DBs and FAISS indexes included, result samples and judge scripts provided.

## Results (Generous Judge)

Global means:

| Metric | Mean (%) |
|---|---:|
| Overall | 79.92 |
| Cat1 (single‑hop factual) | 82.92 |
| Cat2 (temporal) | 60.20 |
| Cat3 (multi‑hop) | 63.24 |
| Cat4 (commonsense) | 87.78 |

Per‑conv means (overall):

| Conv | Mean (%) | Max (%) |
|---:|---:|---:|
| 0 | 86.58 | 87.50 |
| 1 | 81.48 | 82.72 |
| 2 | 84.28 | 85.53 |
| 3 | 76.58 | 76.88 |
| 4 | 75.95 | 76.97 |
| 5 | 77.96 | 78.86 |
| 6 | 76.82 | 78.00 |
| 7 | 85.60 | 86.39 |
| 8 | 76.73 | 77.56 |
| 9 | 76.71 | 77.22 |

Source: `results/release_100runs/metrics_full_100.csv`.

## Architecture (at a glance)

1) Preprocessing: query type, keywords, deterministic synonym expansion (cached).  
2) MCA‑first coverage gate: keep items covering core terms; rank by MCA force (no private formulas/weights disclosed).  
3) Semantics + Sparse: FAISS (BGE‑Large) and BM25.  
4) Union: merge candidates without revealing top‑k/weights.  
5) Final Reranking + Answer: Cross‑Encoder (BAAI/bge‑reranker‑v2‑m3), then concise LLM answer (gpt‑4o‑mini, T=0.0).

```mermaid
flowchart TD
    Q[User Query] --> P1[Preprocessing\n• Classify\n• Keywords\n• Synonyms]
    P1 --> MCA[MCA-first\nCoverage Gate]
    P1 --> FAISS[FAISS\n(BGE-Large)]
    P1 --> BM25[BM25]
    MCA --> U[Union]
    FAISS --> U
    BM25 --> U
    U --> CE[Cross-Encoder\n(bge-reranker)]
    CE --> LLM[gpt-4o-mini\nConcise Answer]
    LLM --> OUT[Final Answer]
```

MCA protects key entities/dates from semantic drift; union keeps recall; CE resolves remaining ambiguity without blowing up top‑k.

## Story (short)

I moved to Columbus 10 months ago. With friends, we tried leaving cell‑tower work to build a closets business. Money was tight; I did handyman gigs. I bought a dream PC (RTX 4090) in installments, launched my favorite games… and felt nothing. Instead, I asked AI how to build a bot, got instructions, and dived into code like never before.

AI helped — and sometimes hallucinated. It hurt. I fought back with tests and metrics. Months later, I hit a breakthrough: my long‑term memory system reaches SOTA on one of the toughest benchmarks. Built largely through AI‑assisted iteration, from scratch, under pressure. This is just the beginning.

## Quickstart

1) `pip install -r requirements.txt`  
2) Copy `.env.example` → `.env`, add keys; DBs/indexes are already in `data/`  
3) Run: `python3 test_v4.64_clean_prompt.py`  
4) Judge: `python3 eval_v4.26_official_generous_judge.py results/<latest>.json`

Docker minimal:

```bash
cd docker/runner
docker build -t locomo-test:latest .
docker run --rm -it -v $(pwd)/../..:/app locomo-test:latest bash
```

## Repository Structure

- `core/`: MCA ranking, cross‑encoder reranker, helpers, config  
- `data/`: per‑conv DBs (`*_full.db`), FAISS (`*.faiss`) and `*_idmap.npy`  
- `results/`: judged JSON samples + `metrics_full_100.csv`  
- `tools/`: build DBs/indexes, verification, summaries  
- `docker/runner/`: minimal repro image  
- `docs/`: MCA description, reproducibility notes

## Contact / Partnerships

Email: Vkuz02452@gmail.com, ViktorAdamCore@pm.me  
Open to productization, PoCs and integrations.

