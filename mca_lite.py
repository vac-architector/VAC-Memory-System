"""
VAC LITE - Simplified MCA (Multi-Candidate Assessment)

This is a LITE implementation of MCA for demonstration.
- Basic keyword matching (no NER, no date parsing)
- Simple coverage scoring
"""

from collections import Counter
import re


def simple_tokenize(text):
    """Simple word tokenization"""
    text = text.lower()
    # Remove punctuation and split
    words = re.findall(r'\b\w+\b', text)
    return set(words)


def mca_lite_filter(query, memories, max_k=50):
    """
    LITE MCA: Simple keyword coverage matching

    How it works:
    1. Extract keywords from query
    2. Score each memory by overlap
    3. Return top-K memories

    Args:
        query: User question
        memories: List of memory dictionaries with 'content' key
        max_k: Maximum number to return

    Returns:
        List of memory indices, sorted by coverage score
    """

    query_keywords = simple_tokenize(query)

    if not query_keywords:
        # No keywords, return first max_k
        return list(range(min(max_k, len(memories))))

    scores = []

    for idx, memory in enumerate(memories):
        content = memory.get('content', '')
        memory_keywords = simple_tokenize(content)

        # Calculate keyword overlap
        overlap = len(query_keywords & memory_keywords)
        coverage = overlap / len(query_keywords) if query_keywords else 0

        scores.append({
            'idx': idx,
            'coverage': coverage,
            'overlap_count': overlap
        })

    # Sort by coverage (descending)
    scores.sort(key=lambda x: x['coverage'], reverse=True)

    # Return top-K indices
    result_indices = [s['idx'] for s in scores[:max_k]]

    return result_indices


if __name__ == "__main__":
    # Demo
    memories = [
        {'content': 'Alice likes pizza and coffee'},
        {'content': 'Bob works as engineer'},
        {'content': 'Alice loves programming'},
        {'content': 'Coffee is great'},
    ]

    query = "Does Alice like pizza?"

    result = mca_lite_filter(query, memories, max_k=10)

    print(f"Query: {query}")
    print(f"Top results indices: {result}")
    for idx in result:
        print(f"  - {memories[idx]['content']}")
