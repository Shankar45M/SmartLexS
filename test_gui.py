"""
Automated GUI and persistence verification test for SmartLex-S.
Tests:
1. Editorial black & gold UI initialization with Agency FB font.
2. Background curve rendering.
3. Sample query: "lexical analyzer tokens".
4. Sample query: "intermediate code optimization".
5. App restart index preservation (SQLite persistence).
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mock dialogs so tests run non-interactively
messagebox.showinfo = lambda title, message: None
messagebox.showwarning = lambda title, message: None
messagebox.showerror = lambda title, message: None

from main import SmartLexApp

def test_redesigned_app():
    print("=== 1. Testing UI Initialization & Design Setup ===")
    root = tk.Tk()
    root.withdraw()
    app = SmartLexApp(root)

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

    # Close first app instance
    root.destroy()
    print("\nFirst app instance closed.")

    print("\n=== 4. Testing App Restart & Persistent Index Preservation ===")
    # Create new fresh Tk instance and SmartLexApp instance without calling load_demo_documents()
    root2 = tk.Tk()
    root2.withdraw()
    app2 = SmartLexApp(root2)

    persisted_items = app2.tree.get_children()
    print(f"Re-launched app loaded {len(persisted_items)} documents from persistent SQLite storage.")
    assert len(persisted_items) == 3, f"Expected 3 persisted documents on restart, got {len(persisted_items)}"

    # Check search directly on the restarted app without re-indexing
    app2.query_var.set("lexical analyzer tokens")
    app2.perform_search()
    restarted_results = app2.tree.get_children()
    assert len(restarted_results) >= 1, "Search should work immediately on restarted app using persistent index"
    top_restarted = app2.tree.item(restarted_results[0], "values")
    assert "lexical" in top_restarted[1].lower()
    print(f"Restarted search verified: {top_restarted[1]} ranked #1 with score {top_restarted[3]}.")

    root2.destroy()
    print("\n>>> ALL REDESIGN & PERSISTENCE TESTS PASSED CLEANLY! <<<")

if __name__ == "__main__":
    test_redesigned_app()
