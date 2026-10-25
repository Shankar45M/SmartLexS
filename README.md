# SmartLex-S: Compiler-Inspired Semantic Document Retrieval

**SmartLex-S** is a lightweight, transparent Python desktop application for semantic document retrieval inspired by compiler design principles (lexical analysis, symbol tables, syntactic token proximity, and scope coverage).

It features a **two-page desktop interface** built in **Tkinter**, using **SQLite** for persistent local storage, extracting text from **PDF, DOCX, and TXT** documents, and computing a fully transparent multi-factor ranking score without relying on paid APIs, cloud services, or heavy AI models.

---

## 🎨 Visual Identity & Architecture

- **Color Palette**: Pure black (`#000000`), secondary surfaces (`#0A0A09`), elevated surfaces (`#11110F`), primary warm-white (`#F3F0E8`), secondary text (`#B5B0A5`), and muted antique-gold accents (`#B69A5A`).
- **Typography**: `Agency FB` for headings, wordmark, section labels, and buttons (with automatic system fallbacks to `Franklin Gothic Medium`, `Century Gothic`, or `Segoe UI`), combined with clean `Segoe UI` for snippets, reading text, and `Consolas` for math.
- **Organic Background Line Art**: Asymmetric, thin, flowing antique-gold curves (`#272115`, `#1D180E`) drawn behind margins and headers.

### Two-Page Architecture (Single Window)
1. **Page 1 — Documents & Search (Home)**:
   - **Header**: Wordmark, subtitle, and dynamic indexed-document library badge.
   - **Document Library**: Import files (`+ Add Documents`), one-click demo loader (`⚡ Index Demo Docs`), refresh, clear index, and live document overview.
   - **Find Relevant Documents**: Prominent query entry with Enter-to-search, `SEARCH DOCUMENTS`, `CLEAR`, and inline validation.
2. **Page 2 — Results & Explainable Evidence**:
   - **Header**: Active query, match count badge, and a prominent `← EDIT QUERY` button that returns to Page 1 with query and state preserved.
   - **Left Column (52%)**: Ranked results table (`ttk.Treeview`) with `RANK`, `DOCUMENT FILE`, `TYPE`, `SCORE`, and factor metrics ($K, S, R, C$).
   - **Right Column (48%)**: Evidence card, final score display, real matched keywords pills, best-matching sentence snippet with keyword highlighting, and step-by-step transparent formula breakdown.

---

## 📐 Compiler-Inspired Architecture & Ranking Formula

SmartLex-S borrows core stages from compiler frontend pipelines:
1. **Lexical Analysis (Scanner)**: Normalizes input text into a token stream, eliminating whitespace/comments, filtering stopwords, and isolating alphanumeric identifiers.
2. **Symbol Table & Persistent Index**: Stores documents, token frequencies, and sentence units in a relational SQLite database.
3. **Syntactic & Scope Analysis**: Evaluates co-occurrence windows and best-sentence context.

### Transparent Ranking Formula
$$\text{FinalScore} = 0.40 \cdot K + 0.25 \cdot S + 0.20 \cdot R + 0.15 \cdot C$$

| Factor | Name | Weight | Compiler Principle | Description |
| :---: | :--- | :---: | :--- | :--- |
| **K** | **Query Coverage** | **40%** | Symbol Presence | Ratio of unique query terms present anywhere in the document symbol table ($K = \frac{|Q \cap D|}{|Q|}$). |
| **S** | **Local Similarity** | **25%** | Term Saturation & Density | Length-normalized sublinear term frequency (BM25-lite) measuring how densely query tokens populate the document. |
| **R** | **Relationship Match** | **20%** | Syntactic Proximity | Checks if adjacent query token pairs appear within a localized clause/sentence window ($\le 15$ words). |
| **C** | **Best-Sentence Coverage** | **15%** | Scope / Statement Match | Fraction of query terms co-located inside the single best matching sentence. Also extracted as evidence snippet. |

> **Note**: All factors $K, S, R, C$ are strictly bounded in the range $[0.0, 1.0]$. The resulting `FinalScore` is always in $[0.0, 1.0]$ ($0\% - 100\%$) and is accompanied by a transparent breakdown in the UI.

---

## 📁 Project Structure

```
SmartLexS/
│
├── main.py                     # Two-page desktop application (Tkinter / ttk)
├── requirements.txt            # Dependency specification (pypdf, python-docx)
├── README.md                   # Complete documentation and evaluation guide
├── test_smartlex.py            # Automated unit test suite (extraction, ranking math, error handling)
├── test_gui.py                 # Automated two-page regression test suite (11 test scenarios)
├── smartlex_index.db           # Persistent SQLite database
├── backup_pre_twopage/         # Backup of working files prior to redesign
│
├── smartlex/
│   ├── __init__.py             # Package init
│   ├── extractors.py           # Text extractors for PDF, DOCX, TXT & tokenizer
│   └── engine.py               # SQLite storage & 4-factor ranking retrieval engine
│
└── demo_documents/             # Sample compiler-themed test documents
    ├── lexical_analysis.txt    # Phase 1: Tokens, Lexer, DFA/NFA, Symbol Table
    ├── syntax_analysis.txt     # Phase 2: CFG, Parsers (LL/LR), AST, Grammar
    └── code_optimization.txt   # Phase 3: Three-Address Code, Optimization passes
```

---

## 🚀 Quick Setup & Launch on Windows

### 1. Prerequisites
- Python 3.10+ (tested and verified on Python 3.14).
- Tkinter (standard library, included with standard Windows Python installations).

### 2. Install Dependencies
Open **Command Prompt** (`cmd.exe`) or **PowerShell** in the project directory:

```powershell
pip install -r requirements.txt
```

*(Installs `pypdf` for PDF extraction and `python-docx` for Word documents).*

### 3. Run Automated Tests
To run the full two-page regression test suite:

```powershell
python test_gui.py
```

To run the core engine unit tests:

```powershell
python test_smartlex.py
```

### 4. Launch Desktop Application
```powershell
python main.py
```

---

## 🖥️ Faculty Demonstration Walkthrough

When presenting SmartLex-S to an evaluator, follow these steps:

1. **Launch the Application**: Run `python main.py`. Notice the sleek editorial black and gold home screen (Page 1) with subtle background curves.
2. **Review Document Library**:
   - The Document Library card shows your indexed documents in SQLite.
   - Click **⚡ Index Demo Docs** to load or refresh the 3 compiler design texts in one click.
3. **Execute Search**:
   - In the **Find Relevant Documents** box, enter: `lexical analyzer tokens`.
   - Click **SEARCH DOCUMENTS** (or hit Enter).
   - The app transitions to **Page 2 (Search Results & Evidence)**.
4. **Inspect Results & Evidence**:
   - `lexical_analysis.txt` is ranked #1 (Final Score: ~`0.9317`).
   - The right panel shows:
     - Document metadata & score.
     - Real matched keywords: `[lexical], [analyzer], [tokens]`.
     - Relevant text snippet from the document with keywords highlighted in warm gold.
     - Complete mathematical formula breakdown showing exact $K, S, R, C$ terms.
5. **Switch Result Selection**:
   - Click row #2 (`syntax_analysis.txt`). Notice the evidence panel instantly updates to show its specific snippet and score calculation.
6. **Edit Query Navigation**:
   - Click **← EDIT QUERY** at the top right.
   - The application transitions back to Page 1 with the previous query retained in the search box and focused for editing.
   - Try another query: `intermediate code optimization`.
   - Result: `code_optimization.txt` is ranked #1 (~`0.9595`).
7. **Empty Query & No-Matches Handling**:
   - Clearing the search box and clicking Search displays an inline warning without navigating.
   - Searching for an unindexed term displays an informative empty state with a direct button back to editing.
8. **Persistence Demonstration**:
   - Close the app and relaunch it (`python main.py`). All indexed files and symbol tables remain intact in SQLite without needing re-indexing.
