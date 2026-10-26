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
    """Runs the evaluation queries against the current SmartLexEngine and records baseline metrics."""
    engine = SmartLexEngine(db_path=db_path)
    
    # Ensure demo documents are present in the database
    docs = engine.get_indexed_documents()
    if len(docs) < 3:
        demo_dir = os.path.join(os.path.dirname(__file__), "demo_documents")
        for f in ["lexical_analysis.txt", "syntax_analysis.txt", "code_optimization.txt"]:
            fpath = os.path.join(demo_dir, f)
            if os.path.exists(fpath):
                engine.index_document(fpath)

    results_summary = []
    
    print("\n" + "=" * 80)
    print("SMARTLEX-S BASELINE BENCHMARK EVALUATION")
    print("=" * 80)

    for item in EVALUATION_QUERIES:
        q_id = item["id"]
        q_str = item["query"]
        category = item["category"]
        expected = item["expected_top_doc"]
        
        matches = engine.search(q_str)
        
        print(f"\n[{q_id}] Category: {category}")
        print(f"Query: \"{q_str}\"")
        print(f"Matches count: {len(matches)}")
        
        if matches:
            top = matches[0]
            top_file = top["filename"]
            score = top["final_score"]
            k = top.get("score_k", 0.0)
            s = top.get("score_s", 0.0)
            r = top.get("score_r", 0.0)
            c = top.get("score_c", 0.0)
            print(f"  Top Result: {top_file} | Score: {score:.4f} (K={k:.2f}, S={s:.2f}, R={r:.2f}, C={c:.2f})")
            print(f"  Matched Keywords: {top['matched_keywords']}")
            print(f"  Snippet: {top['snippet'][:85]}...")
            success = (expected is None) or (top_file == expected)
            print(f"  Expected '{expected}' matched top: {success}")
        else:
            top_file = None
            score = 0.0
            print("  Top Result: None (Zero matches)")
            success = (expected is None)
            print(f"  Expected '{expected}' matched top: {success}")

        results_summary.append({
            "id": q_id,
            "category": category,
            "query": q_str,
            "expected_top_doc": expected,
            "top_doc": top_file,
            "final_score": score,
            "matches_count": len(matches),
            "success": success
        })

    print("\n" + "=" * 80)
    print("BASELINE SUMMARY TABLE")
    print("=" * 80)
    print(f"{'ID':<12} | {'Category':<28} | {'Matches':<7} | {'Top Document':<22} | {'Score':<8} | {'Target Match'}")
    print("-" * 90)
    for res in results_summary:
        print(f"{res['id']:<12} | {res['category']:<28} | {res['matches_count']:<7} | {str(res['top_doc']):<22} | {res['final_score']:<8.4f} | {'PASS' if res['success'] else 'DEFICIT (Expected)'}")
    print("=" * 80)
    
    return results_summary

if __name__ == "__main__":
    record_baseline_benchmarks()
