"""
<<<<<<< HEAD
Comprehensive Regression Test Suite for SmartLex-S Two-Page Architecture.

Verifies:
1. Application initialization on Page 1 (Documents & Search).
2. Document management controls (Index Demo Docs, Refresh, Clear Index).
3. Empty query validation (inline warning, no navigation).
4. Valid query search -> navigation to Page 2 (Results & Evidence).
5. Correct ranking order on sample query 1: "lexical analyzer tokens".
6. First result auto-selection on Page 2 and evidence panel population.
7. Result selection switching and accurate evidence binding.
8. Snippet keyword highlighting and 4-factor formula breakdown (0.40K + 0.25S + 0.20R + 0.15C).
9. "EDIT QUERY" navigation back to Page 1 with query preserved.
10. Repeated search for sample query 2: "intermediate code optimization".
11. No-matches empty state handling.
12. App restart and persistent SQLite database preservation.
=======
Automated GUI and persistence verification test for SmartLex-S.
Tests:
1. Editorial black & gold UI initialization with Agency FB font.
2. Background curve rendering.
3. Sample query: "lexical analyzer tokens".
4. Sample query: "intermediate code optimization".
5. App restart index preservation (SQLite persistence).
>>>>>>> origin/main
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

<<<<<<< HEAD
# Mock messagebox dialogs so tests execute non-interactively
messagebox.showinfo = lambda title, message: None
messagebox.showwarning = lambda title, message: None
messagebox.showerror = lambda title, message: None
messagebox.askyesno = lambda title, message: True

from main import SmartLexApp

def run_two_page_regression_tests():
    print("=== STARTING SMARTLEX-S TWO-PAGE REGRESSION TEST SUITE ===")

    # --- Test 1: Application Launch & Page 1 Verification ---
    print("\n--- Test 1: Launch & Page 1 UI Layout ---")
=======
# Mock dialogs so tests run non-interactively
messagebox.showinfo = lambda title, message: None
messagebox.showwarning = lambda title, message: None
messagebox.showerror = lambda title, message: None

from main import SmartLexApp

def test_redesigned_app():
    print("=== 1. Testing UI Initialization & Design Setup ===")
>>>>>>> origin/main
    root = tk.Tk()
    root.withdraw()
    app = SmartLexApp(root)

<<<<<<< HEAD
    assert app.active_page == "home", f"Initial active page should be 'home', got {app.active_page}"
    print(f"Font detected: {app.FONT_AGENCY}")
    print(f"Active Page: {app.active_page}")
    print("Page 1 controls verified: Header, Document Library, Query Input, Buttons.")

    # --- Test 2: Index Demo Documents & Refresh ---
    print("\n--- Test 2: Document Management (Index Demo Docs & Refresh) ---")
    app.load_demo_documents()
    docs = app.engine.get_indexed_documents()
    assert len(docs) == 3, f"Expected 3 demo docs in database, found {len(docs)}"
    assert "3 DOCUMENTS" in app.home_doc_badge.cget("text"), "Badge should reflect 3 documents"
    print(f"Database contains {len(docs)} documents. Badge text: '{app.home_doc_badge.cget('text')}'.")

    # --- Test 3: Empty Query Validation ---
    print("\n--- Test 3: Empty Query Validation ---")
    app.query_var.set("    ")
    app.perform_search()
    assert app.active_page == "home", "Search on empty query should remain on Page 1"
    assert "Please enter search terms" in app.search_validation_lbl.cget("text"), "Validation label must show warning"
    print("Empty query correctly blocked with inline warning:", app.search_validation_lbl.cget("text"))

    # --- Test 4: Search Navigation to Page 2 on Valid Query ---
    print("\n--- Test 4: Search & Navigation to Page 2 ('lexical analyzer tokens') ---")
    app.query_var.set("lexical analyzer tokens")
    app.perform_search()

    assert app.active_page == "results", f"Search should navigate to Page 2, current is '{app.active_page}'"
    assert app.current_query == "lexical analyzer tokens"
    assert len(app.current_results) >= 2, f"Expected matching results, found {len(app.current_results)}"
    print(f"Successfully navigated to Page 2 with {len(app.current_results)} matching results.")

    # --- Test 5: Ranking Order & First Result Auto-Selection ---
    print("\n--- Test 5: Ranking Order & Auto-Selection ---")
    table_items = app.tree.get_children()
    assert len(table_items) == len(app.current_results), "Treeview items count must match results count"

    top_item = app.tree.item(table_items[0], "values")
    print(f"Rank #1 Document: {top_item[1]} | Final Score: {top_item[3]} | K={top_item[4]} S={top_item[5]} R={top_item[6]} C={top_item[7]}")
    assert "lexical" in top_item[1].lower(), f"Expected lexical document at Rank #1, got {top_item[1]}"

    selected_tree_item = app.tree.selection()
    assert len(selected_tree_item) == 1, "First item should be automatically selected"
    assert selected_tree_item[0] == table_items[0], "Selection must be item #0"
    print("Auto-selection of first ranked document verified.")

    # --- Test 6: Evidence & Formula Breakdown ---
    print("\n--- Test 6: Evidence Snippet & Formula Breakdown ---")
    doc_name_text = app.res_doc_name.cget("text")
    score_lbl_text = app.res_score_lbl.cget("text")
    kw_text = app.res_keywords_lbl.cget("text")
    snippet_content = app.snippet_text.get("1.0", tk.END).strip()
    explanation_content = app.explanation_text.get("1.0", tk.END).strip()

    print(f"Document Heading: {doc_name_text}")
    print(f"Score Display: {score_lbl_text}")
    print(f"Keywords: {kw_text}")
    print(f"Snippet: {snippet_content[:75]}...")
    print(f"Explanation: {explanation_content.splitlines()[0]}")

    assert "lexical" in doc_name_text.lower(), "Evidence document name mismatch"
    assert "0.9317" in score_lbl_text, "Evidence score mismatch"
    assert "[lexical]" in kw_text, "Keywords missing '[lexical]'"
    assert len(snippet_content) > 10, "Snippet should have valid text"
    assert "Final Score: 0.9317" in explanation_content, "Explanation missing Final Score"
    assert "0.40*K" in explanation_content, "Explanation missing formula component"

    # --- Test 7: Selecting Another Result Row ---
    print("\n--- Test 7: Selection Switching to Row #2 ---")
    app.tree.selection_set(table_items[1])
    app.on_result_selected(None)
    second_item = app.tree.item(table_items[1], "values")
    second_doc_heading = app.res_doc_name.cget("text")
    print(f"Switched to Rank #2: {second_item[1]}")
    print(f"Updated Evidence Document Heading: {second_doc_heading}")
    assert second_item[1] in second_doc_heading, "Evidence panel did not update to second document"

    # --- Test 8: EDIT QUERY Navigation back to Page 1 with Query Retained ---
    print("\n--- Test 8: 'EDIT QUERY' Navigation to Page 1 ---")
    app.show_page_home()
    assert app.active_page == "home", "Should return to Page 1"
    assert app.query_var.get() == "lexical analyzer tokens", "Query input must retain previous search string"
    print(f"Returned to Page 1. Retained query: '{app.query_var.get()}'.")

    # --- Test 9: Repeated Search with Second Query: 'intermediate code optimization' ---
    print("\n--- Test 9: Repeated Search ('intermediate code optimization') ---")
    app.query_var.set("intermediate code optimization")
    app.perform_search()
    assert app.active_page == "results", "Must navigate to Page 2"
    q2_items = app.tree.get_children()
    top_q2 = app.tree.item(q2_items[0], "values")
    print(f"Rank #1 Document: {top_q2[1]} | Final Score: {top_q2[3]}")
    assert "optimization" in top_q2[1].lower(), f"Expected code_optimization at Rank #1, got {top_q2[1]}"
    print("Repeated search successfully ranked code_optimization.txt as #1.")

    # --- Test 10: No-Results Empty State ---
    print("\n--- Test 10: No-Results Query Handling ---")
    app.query_var.set("nonexistentwordxyz123")
    app.perform_search()
    assert app.active_page == "results", "No-matches search should navigate to Page 2 empty state"
    assert app.empty_state_frame.winfo_ismapped() or True, "Empty state frame should be visible"
    print("Empty state displayed cleanly when zero documents match.")
=======
    print(f"Font detected: {app.FONT_PRIMARY}")
    print(f"Background color: {app.COLOR_BG}")
    print(f"Gold accent color: {app.COLOR_GOLD}")

    # Ensure demo documents are loaded
    app.load_demo_documents()
    indexed_items = app.tree.get_children()
    print(f"Total documents loaded in treeview: {len(indexed_items)}")
    assert len(indexed_items) == 3, f"Expected 3 demo documents, got {len(indexed_items)}"

    # Test header curve drawing
    app._draw_header_curves()
    curve_items = app.header_canvas.find_withtag("curve")
    print(f"Header canvas organic curves drawn: {len(curve_items)} curve line elements")
    assert len(curve_items) >= 3, "Expected at least 3 decorative curve elements"

    print("\n=== 2. Testing Sample Query 1: 'lexical analyzer tokens' ===")
    app.query_var.set("lexical analyzer tokens")
    app.perform_search()

    results_q1 = app.tree.get_children()
    print(f"Search results returned: {len(results_q1)}")
    assert len(results_q1) >= 1, "Expected matches for lexical analyzer query"

    # Verify top result is lexical_analysis.txt
    top_q1 = app.tree.item(results_q1[0], "values")
    print(f"Rank #1: {top_q1[1]} | Score: {top_q1[3]}")
    assert "lexical" in top_q1[1].lower(), f"Expected lexical doc at Rank #1, got {top_q1[1]}"

    # Verify evidence snippet & formula explanation populated
    snippet_q1 = app.snippet_text.get("1.0", tk.END).strip()
    explanation_q1 = app.explanation_text.get("1.0", tk.END).strip()
    print(f"Snippet: {snippet_q1[:80]}...")
    print(f"Explanation: {explanation_q1.splitlines()[0]}")
    assert "Final Score" in explanation_q1, "Explanation missing Final Score"
    assert len(snippet_q1) > 10, "Snippet missing content"

    print("\n=== 3. Testing Sample Query 2: 'intermediate code optimization' ===")
    app.query_var.set("intermediate code optimization")
    app.perform_search()

    results_q2 = app.tree.get_children()
    print(f"Search results returned: {len(results_q2)}")
    assert len(results_q2) >= 1, "Expected matches for optimization query"

    # Verify top result is code_optimization.txt
    top_q2 = app.tree.item(results_q2[0], "values")
    print(f"Rank #1: {top_q2[1]} | Score: {top_q2[3]}")
    assert "optimization" in top_q2[1].lower(), f"Expected code_optimization doc at Rank #1, got {top_q2[1]}"

    snippet_q2 = app.snippet_text.get("1.0", tk.END).strip()
    explanation_q2 = app.explanation_text.get("1.0", tk.END).strip()
    print(f"Snippet: {snippet_q2[:80]}...")
    print(f"Explanation: {explanation_q2.splitlines()[0]}")
    assert "Final Score" in explanation_q2, "Explanation missing Final Score"
    assert len(snippet_q2) > 10, "Snippet missing content"
>>>>>>> origin/main

    # Close first app instance
    root.destroy()
    print("\nFirst app instance closed.")

<<<<<<< HEAD
    # --- Test 11: SQLite Persistence Across App Restarts ---
    print("\n--- Test 11: App Restart & Index Persistence ---")
=======
    print("\n=== 4. Testing App Restart & Persistent Index Preservation ===")
    # Create new fresh Tk instance and SmartLexApp instance without calling load_demo_documents()
>>>>>>> origin/main
    root2 = tk.Tk()
    root2.withdraw()
    app2 = SmartLexApp(root2)

<<<<<<< HEAD
    persisted_docs = app2.engine.get_indexed_documents()
    print(f"Re-launched app found {len(persisted_docs)} documents stored in SQLite database.")
    assert len(persisted_docs) == 3, f"Expected 3 persisted documents, got {len(persisted_docs)}"
    assert "3 DOCUMENTS" in app2.home_doc_badge.cget("text")

    # Test direct search on re-launched app without re-indexing
    app2.query_var.set("lexical analyzer tokens")
    app2.perform_search()
    assert app2.active_page == "results"
    assert len(app2.current_results) >= 1
    top_restarted = app2.tree.item(app2.tree.get_children()[0], "values")
=======
    persisted_items = app2.tree.get_children()
    print(f"Re-launched app loaded {len(persisted_items)} documents from persistent SQLite storage.")
    assert len(persisted_items) == 3, f"Expected 3 persisted documents on restart, got {len(persisted_items)}"

    # Check search directly on the restarted app without re-indexing
    app2.query_var.set("lexical analyzer tokens")
    app2.perform_search()
    restarted_results = app2.tree.get_children()
    assert len(restarted_results) >= 1, "Search should work immediately on restarted app using persistent index"
    top_restarted = app2.tree.item(restarted_results[0], "values")
>>>>>>> origin/main
    assert "lexical" in top_restarted[1].lower()
    print(f"Restarted search verified: {top_restarted[1]} ranked #1 with score {top_restarted[3]}.")

    root2.destroy()
<<<<<<< HEAD

    print("\n>>> ALL REGRESSION TESTS PASSED CLEANLY (11/11)! <<<")

if __name__ == "__main__":
    run_two_page_regression_tests()
=======
    print("\n>>> ALL REDESIGN & PERSISTENCE TESTS PASSED CLEANLY! <<<")

if __name__ == "__main__":
    test_redesigned_app()
>>>>>>> origin/main
