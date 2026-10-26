"""
SmartLex-S Benchmark Evaluation Harness and Baseline Fixtures.
Records baseline scores and verifies exact, synonym, paraphrase, and out-of-vocabulary query behaviors.
"""

import os
import sys
from typing import List, Dict, Any

# Ensure workspace is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from smartlex.engine import SmartLexEngine

# Fixed evaluation query set representing all target search categories
EVALUATION_QUERIES = [
    {
        "id": "Q1_EXACT",
        "category": "Exact Keyword Match",
        "query": "lexical analyzer tokens",
        "expected_top_doc": "lexical_analysis.txt",
        "description": "Standard lexical search where terms appear literally in the document."
    },
    {
        "id": "Q2_SYNONYM",
        "category": "Synonym / Lexical Variation",
        "query": "scanner tokenization symbol table",
        "expected_top_doc": "lexical_analysis.txt",
        "description": "Uses terminology variations (scanner, tokenization) that overlap with compiler concepts."
    },
    {
        "id": "Q3_PARAPHRASE",
        "category": "Paraphrase / Semantic Match",
        "query": "eliminating unreachable program instructions",
        "expected_top_doc": "code_optimization.txt",
        "description": "Semantic query describing dead code elimination and optimization without literal keyword match."
    },
    {
        "id": "Q4_SYNTAX",
        "category": "Contextual Syntax Parsing",
        "query": "syntax parsing abstract syntax tree grammar",
        "expected_top_doc": "syntax_analysis.txt",
        "description": "Multi-term contextual query matching Phase 2 compiler syntax technique."
    },
    {
        "id": "Q5_UNRELATED",
        "category": "Out-of-Vocabulary / Unrelated",
        "query": "photosynthesis cellular respiration",
        "expected_top_doc": None,
        "description": "Completely out-of-domain biological query that should produce 0 matches or minimal score."
    }
]

def record_baseline_benchmarks(db_path: str = "smartlex_index.db") -> List[Dict[str, Any]]:
    """Runs evaluation queries comparing Baseline (4-factor) vs Hybrid (5-factor) retrieval."""
    engine = SmartLexEngine(db_path=db_path)
    
    # Ensure demo documents are present in the database and embedded
    docs = engine.get_indexed_documents()
    if len(docs) < 3:
        demo_dir = os.path.join(os.path.dirname(__file__), "demo_documents")
        for f in ["lexical_analysis.txt", "syntax_analysis.txt", "code_optimization.txt"]:
            fpath = os.path.join(demo_dir, f)
            if os.path.exists(fpath):
                engine.index_document(fpath)
    else:
        engine.backfill_embeddings()

    results_summary = []
    
    print("\n" + "=" * 80)
    print("SMARTLEX-S RETRIEVAL BENCHMARK EVALUATION (BASELINE vs HYBRID)")
    print("=" * 80)

    for item in EVALUATION_QUERIES:
        q_id = item["id"]
        q_str = item["query"]
        category = item["category"]
        expected = item["expected_top_doc"]
        
        matches_hybrid = engine.search(q_str, hybrid_scoring=True)
        matches_baseline = engine.search(q_str, hybrid_scoring=False)
        
        print(f"\n[{q_id}] Category: {category}")
        print(f"Query: \"{q_str}\"")
        
        if matches_hybrid:
            top_h = matches_hybrid[0]
            top_h_file = top_h["filename"]
            score_h = top_h["final_score"]
            k = top_h.get("score_k", 0.0)
            s = top_h.get("score_s", 0.0)
            r = top_h.get("score_r", 0.0)
            c = top_h.get("score_c", 0.0)
            e = top_h.get("score_e", 0.0)
            success_h = (expected is None) or (top_h_file == expected)
            print(f"  Hybrid Top Result : {top_h_file} | Score: {score_h:.4f} (K={k:.2f}, S={s:.2f}, R={r:.2f}, C={c:.2f}, E={e:.2f})")
            print(f"  Snippet: {top_h['snippet'][:85]}...")
        else:
            top_h_file = None
            score_h = 0.0
            success_h = (expected is None)

        top_b_score = matches_baseline[0]["final_score"] if matches_baseline else 0.0
        top_b_file = matches_baseline[0]["filename"] if matches_baseline else None

        results_summary.append({
            "id": q_id,
            "category": category,
            "query": q_str,
            "expected_top_doc": expected,
            "baseline_score": top_b_score,
            "baseline_doc": top_b_file,
            "hybrid_score": score_h,
            "hybrid_doc": top_h_file,
            "matches_count": len(matches_hybrid),
            "success": success_h
        })

    print("\n" + "=" * 96)
    print("COMPARATIVE BENCHMARK SUMMARY (BASELINE 4-FACTOR vs HYBRID 5-FACTOR)")
    print("=" * 96)
    print(f"{'ID':<12} | {'Category':<28} | {'Target Expected':<22} | {'Base Score':<10} | {'Hybrid Score':<12} | {'Status'}")
    print("-" * 96)
    for res in results_summary:
        print(f"{res['id']:<12} | {res['category']:<28} | {str(res['expected_top_doc']):<22} | {res['baseline_score']:<10.4f} | {res['hybrid_score']:<12.4f} | {'PASS' if res['success'] else 'FAIL'}")
    print("=" * 96)
    
    return results_summary

if __name__ == "__main__":
    record_baseline_benchmarks()
