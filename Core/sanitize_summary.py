#!/usr/bin/env python3
"""
Normalize summary.pipeline and summary.architecture fields in result JSON files.

Usage:
  python3 sanitize_summary.py <path/to/result1.json> [<path/to/result2.json> ...]
"""

import json
import sys
from pathlib import Path


PIPELINE_NAME = "VAC Memory System v1"
ARCHITECTURE = [
    "1. Query Classification",
    "2. LLM Synonym Expansion (qwen2.5:14b)",
    "3. [TARGET] MCA-first filter",
    "4. [TARGET] FAISS top-k (semantic, BGE-large 1024D)",
    "5. [TARGET] BM25 top-k (sparse)",
    "6. Union(MCA, FAISS, BM25) -> ~112 docs",
    "7. [FIRE] Cross-Encoder DIRECT reranking (ALL ~112 docs -> top-15)",
    "8. gpt-4o-mini answer (T=0.0, max_tokens=150)   MEM0 OFFICIAL!",
]
EMBED_MODEL = "bge-large-en-v1.5"
EMBED_DIM = 1024


def sanitize_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    summary["pipeline"] = PIPELINE_NAME
    summary["architecture"] = ARCHITECTURE
    summary["embedding_model"] = EMBED_MODEL
    summary["embedding_dim"] = EMBED_DIM
    data["summary"] = summary

    # Drop config block (internal tuning details)
    if "config" in data:
        data.pop("config", None)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp_path.replace(path)
    print(f"Sanitized: {path}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 sanitize_summary.py <result1.json> [<result2.json> ...]")
        return 1
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"Skip (not found): {path}")
            continue
        sanitize_file(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
