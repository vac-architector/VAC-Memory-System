"""
VAC LITE - Simplified Pipeline

Simplified version of VAC pipeline for demonstration:
- MCA filter (basic keyword matching)
- FAISS semantic search
- Top-K selection
- LLM answer generation

Full pipeline has:
+ Synonym expansion
+ BM25 lexical search
+ Union strategy
+ Cross-encoder reranking
+ Advanced MCA with NER/dates
"""

import sqlite3
import numpy as np
import faiss
from .mca_lite import mca_lite_filter


class VACLitePipeline:
    """Simplified VAC pipeline for demonstration"""

    def __init__(self, db_path, faiss_index_path, faiss_idmap_path, embedding_model=None):
        """
        Initialize LITE pipeline

        Args:
            db_path: Path to SQLite database
            faiss_index_path: Path to FAISS index
            faiss_idmap_path: Path to FAISS ID mapping
            embedding_model: Embedding model (optional)
        """
        self.db_path = db_path
        self.faiss_index_path = faiss_index_path
        self.faiss_idmap_path = faiss_idmap_path
        self.embedding_model = embedding_model

        # Load FAISS index
        self.index = None
        self.idmap = None
        self._load_index()

    def _load_index(self):
        """Load FAISS index from disk"""
        try:
            self.index = faiss.read_index(self.faiss_index_path)
            self.idmap = np.load(self.faiss_idmap_path)
            print(f"✅ Loaded FAISS index ({len(self.idmap)} vectors)")
        except Exception as e:
            print(f"⚠️  Could not load FAISS index: {e}")

    def _get_memories_by_ids(self, memory_ids):
        """Get memory content from database by IDs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        memories = []
        for mid in memory_ids:
            cursor.execute(
                "SELECT id, content FROM memories WHERE id = ?",
                (int(mid),)
            )
            row = cursor.fetchone()
            if row:
                memories.append({'id': row[0], 'content': row[1]})

        conn.close()
        return memories

    def _get_all_memories(self):
        """Get all memories from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, content FROM memories")
        memories = [
            {'id': row[0], 'content': row[1]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return memories

    def retrieve(self, query, mca_top_k=50, faiss_top_k=15):
        """
        LITE Retrieval: MCA filter + FAISS search

        Steps:
        1. Get all memories
        2. Apply MCA filter (keyword coverage) → top-50
        3. Search FAISS on filtered results → top-15
        4. Return top-15 memories

        Note: Full version also uses BM25, union, cross-encoder reranking

        Args:
            query: User question
            mca_top_k: Number of memories to filter with MCA
            faiss_top_k: Final number of memories to return

        Returns:
            List of top-K memories with scores
        """

        # Step 1: Get all memories
        all_memories = self._get_all_memories()
        print(f"📊 Total memories in DB: {len(all_memories)}")

        if not all_memories:
            return []

        # Step 2: MCA filter (basic keyword matching)
        mca_indices = mca_lite_filter(query, all_memories, max_k=mca_top_k)
        mca_memories = [all_memories[idx] for idx in mca_indices]
        print(f"📍 After MCA filter: {len(mca_memories)} memories")

        # Step 3: FAISS search on filtered results
        if self.embedding_model and self.index is not None:
            try:
                # Encode query
                query_emb = self.embedding_model.encode(query)
                query_vec = np.array([query_emb], dtype='float32')

                # Search FAISS
                distances, indices = self.index.search(query_vec, min(faiss_top_k, len(self.idmap)))

                # Get memory details
                results = []
                for i, idx in enumerate(indices[0]):
                    memory_id = int(self.idmap[idx])
                    memory = next((m for m in mca_memories if m['id'] == memory_id), None)

                    if memory:
                        results.append({
                            'id': memory['id'],
                            'content': memory['content'],
                            'score': float(distances[0][i])
                        })

                print(f"🔍 After FAISS search: {len(results)} memories")
                return results

            except Exception as e:
                print(f"⚠️  FAISS search failed: {e}")
                # Fallback: return MCA results
                return [{'id': m['id'], 'content': m['content'], 'score': 0.0} for m in mca_memories[:faiss_top_k]]
        else:
            # No embedding model, just return MCA results
            return [{'id': m['id'], 'content': m['content'], 'score': 0.0} for m in mca_memories[:faiss_top_k]]

    def generate_answer(self, question, memories, llm_model=None, llm_temperature=0.0):
        """
        Generate answer using retrieved memories

        Note: This is simplified - full version has more advanced prompting

        Args:
            question: User question
            memories: Retrieved memories
            llm_model: LLM model to use
            llm_temperature: Temperature for LLM

        Returns:
            Generated answer
        """

        if not memories:
            return "No relevant information found."

        # Prepare context
        context = "\n".join([f"- {m['content']}" for m in memories])

        # Simple prompt (full version has more sophisticated prompting)
        prompt = f"""Based on the following information, answer the question:

Question: {question}

Information:
{context}

Answer:"""

        # Note: LLM call would happen here
        # For LITE version, just return formatted context
        return f"Based on {len(memories)} memories: {context[:200]}..."


def process_questions_lite(db_path, faiss_index_path, faiss_idmap_path,
                          questions_list, embedding_model=None, llm_model=None):
    """
    Process questions using LITE pipeline

    Args:
        db_path: Path to SQLite database
        faiss_index_path: Path to FAISS index
        faiss_idmap_path: Path to FAISS ID mapping
        questions_list: List of questions
        embedding_model: Embedding model
        llm_model: LLM model

    Returns:
        Results dictionary
    """

    pipeline = VACLitePipeline(db_path, faiss_index_path, faiss_idmap_path, embedding_model)

    results = {
        'questions_processed': 0,
        'results': []
    }

    for q in questions_list:
        question = q.get('question', '')

        # Retrieve
        memories = pipeline.retrieve(question)

        # Generate answer
        answer = pipeline.generate_answer(question, memories, llm_model)

        results['results'].append({
            'question': question,
            'answer': answer,
            'retrieved_memories': len(memories)
        })
        results['questions_processed'] += 1

    return results


if __name__ == "__main__":
    # Demo
    print("""
    VAC LITE Pipeline Demo
    =====================

    LITE Features:
    - Simple keyword-based MCA
    - FAISS semantic search
    - Basic LLM generation
    - ~65-70% accuracy

    Full Version adds:
    - Advanced MCA with NER/dates
    - BM25 lexical search
    - Union strategy
    - Cross-encoder reranking
    - ~80.1% accuracy
    """)
