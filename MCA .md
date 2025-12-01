MCA: Entity Coverage as a Memory Retrieval Gate

The Problem With Vector Search
Vector databases (FAISS, Pinecone) excel at finding semantically similar content. But they have a critical blind spot: they return documents that are semantically close but factually wrong.
Example:

* Query: "Where did I meet Alice?"

* FAISS returns: "I met Bob at the coffee shop" (high cosine similarity—same structure, location mention)

* Problem: The query asks about Alice, not Bob. FAISS matched the pattern but missed the entity.

BM25 catches "Alice" via exact match, but misses paraphrasing ("encountered Alice", "ran into her").
MCA: A Pre-Filter That Stops False Positives
Multi-Candidate Assessment (MCA) is a gate that runs before expensive vector search. Instead of semantic matching, it asks a simpler question: "How many of the query's key terms appear in this memory?"

The core algorithm:


```python
def calculate_query_coverage(query_keywords: set, memory_keywords: set) -> float:
    if not query_keywords:
        return 0.0
    intersection = len(query_keywords & memory_keywords)
    return intersection / len(query_keywords)

# Usage
query_keywords = extract_keywords("Where did I meet Alice?")  # → {"alice", "meet"}

for memory in all_memories:
    memory_keywords = extract_keywords(memory['content'])
    coverage = calculate_query_coverage(query_keywords, memory_keywords)
    
    if coverage < 0.1:  # Threshold
        continue  # Skip—don't waste FAISS compute
    
    candidates.append(memory)
```

The physics-inspired ranking (from the codebase):
python

```python
distance = max(DELTA, 1.0 - coverage)
mass = coverage * importance_weight
force = G * (query_mass * memory_mass) / (distance ** 2 + DELTA)
```

Memories with higher entity overlap have stronger "gravitational pull" toward the query.

---

**Benchmark Results**

On LoCoMo (long-context memory benchmark, 100 validated runs):

| Pipeline | Accuracy |
|----------|----------|
| FAISS + BM25 + Cross-Encoder | 68-74% |
| **MCA gate + FAISS + BM25 + Cross-Encoder** | **80.1%** |
| Mem0 (reported) | 68% |
| Letta (reported) | 74% |

The +6-12% gain comes from MCA eliminating false positives early. Instead of cross-encoder reranking 500 semantically-similar-but-wrong documents, it reranks ~120 entity-relevant ones.

---

**The Full Pipeline**
```
Query: "Where did I meet Alice?"
         ↓
[1] Keyword extraction: {"alice", "meet"}
         ↓
[2] MCA-FIRST FILTER (coverage ≥ 0.1)
    1000 memories → ~30 candidates
         ↓
[3] FAISS (BGE-large, 1024D) 
    Adds semantically similar: "visited Alice", "encountered her"
    → 100 candidates
         ↓
[4] BM25 
    Catches keyword variations FAISS missed
    → 40 more candidates
         ↓
[5] Union + Deduplication → ~120 unique
         ↓
[6] Cross-Encoder Reranking (bge-reranker-v2-m3)
    120 → 15 best
         ↓
[7] LLM Answer (gpt-4o-mini, T=0.0)
````

Why this order matters:

* MCA alone misses paraphrasing ("Alice" vs "her")

* FAISS alone returns wrong entities with right patterns

* BM25 alone misses semantic variations

* Cross-encoder is expensive—run it on filtered candidates, not everything

MCA vs BM25 vs Vector Search

```
| Aspect              | BM25                   | Vector (FAISS)         | MCA             |
| ------------------- | ---------------------- | ---------------------- | --------------- |
| Measures            | TF-IDF term importance | Cosine similarity      | Entity coverage |
| Paraphrasing        | ❌                      | ✅                      | ❌               |
| Entity preservation | ✅                      | ❌                      | ✅               |
| Speed               | Fast                   | Medium (GPU)           | Very fast       |
| Solo accuracy       | ~50%                   | ~65–70%                | ~40%            |
| Role in pipeline    | Keyword backup         | Semantic understanding | Pre-filter gate |

```

MCA isn't meant to replace anything. It's a gate that reduces the candidate pool before expensive operations.
Why Not Just Use MCA?
MCA alone scores ~40-50% because:

1. Typos/variations: Query "Alice", memory has "Alicia" → coverage=0 → skipped

2. Pronouns: "Where did I meet her?" → no direct entity match

3. Paraphrasing: "encountered" vs "met" needs embeddings

MCA is a filter, not a retriever.
Implementation Details
From the actual codebase—the stopword list matters:
python

```python
stopwords = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'what', 'when', 'where', 'who',
    'which', 'how', 'to', 'of', 'in', 'on', 'at', 'by', 'for',
    'with', 'from', 'about', 'as', 'into', 'through', 'during',
    'that', 'this', 'these', 'those', 'and', 'or', 'but', 'if'
}

def extract_keywords_simple(text: str) -> set:
    words = text.lower().split()
    keywords = set()
    for word in words:
        cleaned = word.strip('?.,!;:()[]{}"\'-')
        if len(cleaned) >= 3 and cleaned not in stopwords:
            keywords.add(cleaned)
    return keywords
```

The threshold (0.1) is tuned—too high filters good candidates, too low lets noise through.
 




