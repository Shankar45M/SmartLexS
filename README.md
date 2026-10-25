# SmartLex-S: Compiler-Inspired Semantic Document Retrieval

**SmartLex-S** is a lightweight, transparent Python desktop application for semantic document retrieval inspired by compiler design principles (lexical analysis, symbol tables, syntactic token proximity, and scope coverage).

It runs locally with **Tkinter**, uses **SQLite** for persistent storage, extracts text from **PDF, DOCX, and TXT** documents, and computes a fully transparent multi-factor ranking score without relying on paid APIs, cloud services, or heavy AI models.

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
| **R** | **Relationship Match** | **20%** | Syntactic Proximity | Checks if adjacent query token pairs appear within a localized window ($\le 6$ words) in the text. |
| **C** | **Best-Sentence Coverage** | **15%** | Scope / Statement Match | Fraction of query terms co-located inside the single best matching sentence. Also extracted as evidence snippet. |

> **Note**: All factors $K, S, R, C$ are strictly bounded in the range $[0.0, 1.0]$. The resulting `FinalScore` is always in $[0.0, 1.0]$ ($0\% - 100\%$) and is accompanied by a transparent breakdown in the UI.

---

## 📁 Project Structure

```
SmartLexS/
│
├── main.py                     # Desktop GUI application (Tkinter / ttk)
├── requirements.txt            # Dependency specification (pypdf, python-docx)
├── README.md                   # Complete documentation and evaluation guide
├── test_smartlex.py            # Automated test suite (indexing, ranking, error handling)
├── test_gui.py                 # Automated UI verification script
├── smartlex_index.db           # Persistent SQLite database
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

*(This installs `pypdf` for PDF extraction and `python-docx` for Word documents).*

### 3. Run Automated Tests (Optional)
To verify database indexing, retrieval, and ranking logic:

```powershell
python test_smartlex.py
```

### 4. Launch Desktop Application
```powershell
python main.py
```

---

## 🖥️ Faculty Demonstration Guide

When presenting SmartLex-S to an evaluator, follow these steps:

1. **Launch the Application**: Run `python main.py`.
2. **Index Demo Documents**:
   - Click the **⚡ Index Demo Docs** button at the top right.
   - SmartLex-S will automatically load the three sample documents covering:
     1. Lexical Analysis
     2. Syntax Analysis & Parsing
     3. Code Optimization
3. **Execute Compiler-Themed Queries**:
   - **Query 1**: `lexical analysis tokens scanner`
     - Observe: `lexical_analysis.txt` achieves the highest score (~0.75+).
     - Click the row to inspect the **Evidence Panel**: view the highlighted sentence and the transparent $0.40K + 0.25S + 0.20R + 0.15C$ calculation.
   - **Query 2**: `syntax analysis parsing abstract syntax tree`
     - Observe: `syntax_analysis.txt` ranks #1 (~0.85+).
   - **Query 3**: `dead code elimination optimization basic blocks`
     - Observe: `code_optimization.txt` ranks #1 (~0.83+).
4. **Import Custom Documents**:
   - Click **➕ Add Documents** to import your own `.pdf`, `.docx`, or `.txt` files.
   - Notice instant extraction and persistent SQLite indexing.
5. **Demonstrate Friendly Error Handling**:
   - Search for a term that does not exist (e.g. `quantum thermodynamics`): a friendly message explains that no documents matched.
   - Attempting to import an unreadable or corrupt file presents a descriptive notification rather than crashing.
