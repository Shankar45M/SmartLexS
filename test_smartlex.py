"""
Verification test script for SmartLex-S.
Tests indexing, text extraction, search ranking formula, and error handling.
"""

import os
import sys

# Ensure workspace is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from smartlex.engine import SmartLexEngine
from smartlex.extractors import extract_text_from_file, tokenize_text, ExtractionError

def run_tests():
    print("=== 1. Testing Document Extraction & Tokenization ===")
    demo_dir = os.path.join(os.path.dirname(__file__), "demo_documents")
    doc1 = os.path.join(demo_dir, "lexical_analysis.txt")
    doc2 = os.path.join(demo_dir, "syntax_analysis.txt")
    doc3 = os.path.join(demo_dir, "code_optimization.txt")

    for fpath in [doc1, doc2, doc3]:
        assert os.path.exists(fpath), f"File {fpath} does not exist"
        text, ftype = extract_text_from_file(fpath)
        tokens = tokenize_text(text)
        print(f"Extracted {os.path.basename(fpath)}: {len(tokens)} content tokens, type={ftype}")
        assert len(tokens) > 20, "Tokens should be more than 20"

    print("\n=== 2. Testing SQLite Engine Indexing ===")
    test_db = "test_smartlex.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    engine = SmartLexEngine(db_path=test_db)
    for fpath in [doc1, doc2, doc3]:
        info = engine.index_document(fpath)
        print(f"Indexed {info['filename']}: id={info['doc_id']}, tokens={info['token_count']}")

    indexed = engine.get_indexed_documents()
    assert len(indexed) == 3, f"Expected 3 documents, got {len(indexed)}"
    print(f"Successfully verified 3 documents in persistent SQLite index.")

    print("\n=== 3. Testing Semantic Search & Transparent Ranking Formulas ===")
    test_queries = [
        "lexical analysis scanner tokenization",
        "syntax analysis parsing abstract syntax tree",
        "intermediate code optimization dead code elimination",
        "nonexistenttermxyz"
    ]

    print("\n--- 3a. Testing Hybrid 5-Factor Formula (0.25*K + 0.15*S + 0.15*R + 0.15*C + 0.30*E) ---")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = engine.search(query, hybrid_scoring=True)
        print(f"Total matching results: {len(results)}")
        for r in results:
            print(f"  Rank #{results.index(r)+1}: {r['filename']} | Final={r['final_score']} (K={r['score_k']}, S={r['score_s']}, R={r['score_r']}, C={r['score_c']}, E={r['score_e']})")
            print(f"    Snippet: {r['snippet'][:80]}...")
            
            # Verify 5-factor hybrid formula: 0.25*K + 0.15*S + 0.15*R + 0.15*C + 0.30*E
            calculated = (0.25 * r['score_k']) + (0.15 * r['score_s']) + (0.15 * r['score_r']) + (0.15 * r['score_c']) + (0.30 * r['score_e'])
            calculated = max(0.0, min(1.0, calculated))
            assert abs(calculated - r['final_score']) < 0.001, f"Hybrid formula mismatch: {calculated} vs {r['final_score']}"
            assert 0.0 <= r['final_score'] <= 1.0, "Score must be bounded in [0.0, 1.0]"

    print("\n--- 3b. Testing Baseline 4-Factor Formula (0.40*K + 0.25*S + 0.20*R + 0.15*C) ---")
    for query in test_queries:
        results_baseline = engine.search(query, hybrid_scoring=False)
        for r in results_baseline:
            calc_base = (0.40 * r['score_k']) + (0.25 * r['score_s']) + (0.20 * r['score_r']) + (0.15 * r['score_c'])
            calc_base = max(0.0, min(1.0, calc_base))
            assert abs(calc_base - r['final_score']) < 0.001, f"Baseline formula mismatch: {calc_base} vs {r['final_score']}"

    # Verify query 1 ranks lexical_analysis.txt first
    q1_results = engine.search("lexical analyzer token stream")
    assert q1_results[0]["filename"] == "lexical_analysis.txt", "Lexical doc should rank #1 for lexical query"

    # Verify query 2 ranks syntax_analysis.txt first
    q2_results = engine.search("parse tree grammar syntax analysis")
    assert q2_results[0]["filename"] == "syntax_analysis.txt", "Syntax doc should rank #1 for syntax query"

    # Verify query 3 ranks code_optimization.txt first
    q3_results = engine.search("dead code elimination peephole optimization")
    assert q3_results[0]["filename"] == "code_optimization.txt", "Optimization doc should rank #1 for optimization query"

    print("\n=== 4. Testing Error Handling ===")
    try:
        extract_text_from_file("non_existent_file.xyz")
        assert False, "Should have raised ExtractionError"
    except ExtractionError as e:
        print(f"Caught expected friendly error: {e}")

    # Clean up test db
    import gc
    del engine
    gc.collect()
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
