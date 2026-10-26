# SmartLex-S: Compiler-Inspired Hybrid Intelligent Search System

**SmartLex-S** is an offline, explainable hybrid intelligent document retrieval desktop application. It unifies **compiler-inspired lexical analysis and symbol tables** with **dense semantic embeddings**, **domain-aware synonym expansion**, a transparent **5-factor ranking formula**, and an optional **local Ollama LLM integration** with rapid offline fallback.

Built in Python with a bespoke two-page editorial desktop interface (**Tkinter/ttk**) styled in obsidian black (`#000000`) and muted antique-gold (`#B69A5A`), SmartLex-S executes **100% locally on CPU without paid APIs, mandatory cloud connectivity, or external vector databases**.

---

## 🏛️ System Architecture

SmartLex-S combines compiler frontend principles with modern neural information retrieval:

```
[ Documents: TXT, PDF, DOCX ]
             │
             ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. LEXICAL ANALYSIS & COMPILER EXTRACTION (smartlex/extractors.py)     │
│  • Normalization, whitespace/comment stripping, regex tokenization      │
│  • Stopword elimination & identifier isolation                         │
│  • Sentence segmentation for localized scope tracking                  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
┌────────────────────────────────────────┐  ┌────────────────────────────────────────┐
│ 2. SYMBOL TABLE & PERSISTENCE (SQLite) │  │ 3. DENSE SEMANTIC EMBEDDINGS           │
│  • documents: metadata & raw text      │  │    (smartlex/embeddings.py)            │
│  • doc_tokens: token frequencies       │  │  • all-MiniLM-L6-v2 (384-dim dense)    │
│  • doc_sentences: sentence index       │  │  • Mean pooling + L2 normalization     │
│  • doc_embeddings: serialized vectors  │  │  • CPU inference (~5-15ms/doc)         │
└────────────────────┬───────────────────┘  └───────────────────┬────────────────────┘
                     │                                          │
                     └───────────────────┬──────────────────────┘
                                         │
┌────────────────────────────────────────▼───────────────────────────────────┐
│ 4. HYBRID QUERY PROCESSING & RETRIEVAL ENGINE (smartlex/engine.py)         │
│                                                                            │
│  [User Query] ──► [Synonym Expansion Engine (smartlex/synonyms.py)]        │
│                    • NLTK WordNet POS-filtered synonyms                    │
│                    • Compiler Domain Thesaurus (e.g. parser -> AST/CFG)    │
│                    • 0.70x synonym score attenuation                       │
│                                                                            │
│  [5-Factor Transparent Ranking Formula]                                    │
│   FinalScore = 0.25*K + 0.15*S + 0.15*R + 0.15*C + 0.30*E ∈ [0.0, 1.0]      │
│     ├── K (25%): Query Symbol Table Coverage                               │
│     ├── S (15%): Length-Normalized Sublinear Term Density                  │
│     ├── R (15%): Syntactic Proximity / Adjacent Pair Match (window ≤ 15)   │
│     ├── C (15%): Best-Sentence Context Scope Match & Extracted Snippet     │
│     └── E (30%): Semantic Cosine Similarity (Query vs Doc Vector)          │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
┌────────────────────────────────────────┐  ┌────────────────────────────────────────┐
│ 5. EDITORIAL TWO-PAGE DESKTOP UI       │  │ 6. LOCAL LLM SYNTHESIS & FALLBACK      │
│    (main.py - Tkinter / ttk)           │  │    (smartlex/llm.py)                   │
│  • Page 1: Document Library & Query    │  │  • Probe Ollama (http://localhost:11434│
│  • Page 2: 52/48 Split Results Table   │  │  • Non-blocking probe (1.5s timeout)   │
│    & Explainable Evidence Panel        │  │  • Grounded anti-hallucination prompt  │
│  • Organic antique-gold line art       │  │  • Rapid 0.01ms extractive fallback    │
│  • Verbatim snippet highlighting       │  │    when Ollama daemon is offline       │
└────────────────────────────────────────┘  └────────────────────────────────────────┘
```

---

## 📐 Transparent 5-Factor Hybrid Ranking Formula

Every document is ranked using a mathematically bounded scoring formula where $\text{FinalScore} \in [0.0, 1.0]$ ($0\% \text{ to } 100\%$):

$$\mathbf{FinalScore} = 0.25 \cdot K + 0.15 \cdot S + 0.15 \cdot R + 0.15 \cdot C + 0.30 \cdot E$$

### Signal Breakdown

| Signal | Factor Name | Weight | Compiler Principle | Mathematical Definition & Description |
| :---: | :--- | :---: | :--- | :--- |
| **K** | **Query Coverage** | **25%** | Symbol Presence | Ratio of unique query terms present in the document's symbol table ($K = \frac{\|Q \cap D\|}{\|Q\|}$). Synonym matches receive attenuated weight ($0.70\times$). |
| **S** | **Local Similarity** | **15%** | Term Saturation & Density | Length-normalized sublinear term frequency: $S = \frac{\sum_{t \in Q} \sqrt{\text{count}(t)}}{\sqrt{\text{token\_count}} \cdot \text{scale}}$. Prevents long-document frequency gaming. |
| **R** | **Relationship Match** | **15%** | Syntactic Proximity | Checks if adjacent query token pairs $(q_i, q_{i+1})$ co-occur within a localized sliding window ($\le 15$ words), reflecting syntactic collocations. |
| **C** | **Sentence Context** | **15%** | Local Scope Resolution | Identifies the single sentence maximizing query term co-location. The best sentence is extracted as the verbatim evidence snippet. |
| **E** | **Semantic Similarity** | **30%** | Latent Concept Alignment | Cosine similarity between 384-dimensional dense embeddings of query and document: $E = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$. Mapped from $[-1, 1]$ to $[0, 1]$. |

> **Baseline vs. Hybrid Mode**: For educational and benchmark comparisons, the engine supports both the hybrid 5-factor model and the baseline 4-factor compiler model ($0.40K + 0.25S + 0.20R + 0.15C$) via `hybrid_scoring=False`.

---

## 🔬 Benchmark Evaluation: Baseline vs. Hybrid

Evaluation was performed against 5 canonical test categories comparing the baseline 4-factor compiler model against the upgraded hybrid 5-factor retrieval model (`python test_fixtures.py`):

| ID | Test Category | Query | Target Expected Document | Baseline Score | Hybrid Score | Improvement & Analysis |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **Q1_EXACT** | Exact Keyword Match | `"lexical analyzer tokens"` | `lexical_analysis.txt` | `0.9317` | **`0.8960`** | **PASS** — Both rank target #1 with massive confidence. Hybrid provides balanced semantic validation ($E=0.79$). |
| **Q2_SYNONYM** | Synonym / Lexical Variation | `"scanner tokenization symbol table"` | `lexical_analysis.txt` | `0.6723` | **`0.6200`** | **PASS** — Synonym attenuation ($0.70\times$) and domain mapping correctly credit `"scanner"` $\to$ `"lexical analyzer"`. Target ranks #1. |
| **Q3_PARAPHRASE** | Paraphrase / Semantic Match | `"eliminating unreachable program instructions"` | `code_optimization.txt` | `0.4033` | **`0.4215`** | **PASS** — Overcomes the classic **vocabulary mismatch problem**. Dense semantic embedding ($E=0.51$) decisively ranks optimization #1 despite zero exact keyword overlap with `"unreachable"`. |
| **Q4_SYNTAX** | Contextual Syntax Parsing | `"syntax parsing abstract syntax tree grammar"` | `syntax_analysis.txt` | `0.8662` | **`0.8112`** | **PASS** — High syntactic collocation ($R=0.80$) and dense semantic match ($E=0.68$) rank target #1. |
| **Q5_UNRELATED** | Out-of-Vocabulary / Unrelated | `"photosynthesis cellular respiration"` | *None* | `0.0000` | **`0.0442`** | **PASS** — Zero keyword matches ($K=0, S=0, R=0, C=0$) with negligible semantic residual noise ($0.04$). Accurately rejected as irrelevant. |

---

## 🧠 Explainability & Local LLM Integration

### 1. Document-Grounded Explainability
SmartLex-S prioritizes **truthful explainability**:
- **Verbatim Snippets**: Extracts the exact highest-scoring sentence directly from the indexed document—never paraphrased or fabricated.
- **Visual Highlighting**: Query terms and recognized synonyms are dynamically highlighted in warm gold inside the snippet viewer.
- **Mathematical Transparency**: Full mathematical breakdown showing exact decimal contributions of $K, S, R, C, E$.

### 2. Local Ollama LLM with Instant Extractive Fallback
SmartLex-S connects to local Ollama instances (`http://localhost:11434`) with strict fail-safe guarantees:
- **Zero Hallucination Grounding**: Prompt constraints enforce that answers be strictly derived from the extracted excerpt.
- **Non-Blocking Health Check**: 1.5s probe with lazy caching.
- **Instant Offline Fallback**: If Ollama is not installed or offline, the UI instantly falls back to structured extractive passage summaries in **$<0.02\text{ms}$** without UI freezing.

---

## 🎨 Editorial Desktop Interface Design

The Tkinter desktop interface (`main.py`) follows an editorial black-and-gold visual language:
- **Palette**: Pure obsidian black background (`#000000`), subtle cards (`#0A0A09`, `#11110F`), warm-white reading text (`#F3F0E8`), and muted antique-gold accents (`#B69A5A`).
- **Typography**: Header hierarchy using `Agency FB` (with fallback to `Franklin Gothic Medium` or `Segoe UI`), `Georgia`/`Segoe UI` for snippets, and `Consolas` for math formulas.
- **Organic Geometry**: Subtle antique-gold line art dynamically rendered on the canvas background.
- **Two-Page Navigation**:
  - **Page 1 (Home)**: Document library management (`+ Add Documents`, `⚡ Index Demo Docs`, `Clear Index`), library badge, live status indicators, search query input, and inline error validation.
  - **Page 2 (Results & Evidence)**: 52% ranked results table with full factor breakdown ($K, S, R, C, E$), 48% explainable evidence panel, interactive row selection, snippet highlighting, live AI synthesis card, and an **`← EDIT QUERY`** button preserving previous query state.

---

## 📁 Repository Structure

```
SmartLexS/
│
├── main.py                     # Two-page desktop application (Tkinter / ttk)
├── requirements.txt            # Dependency specification (torch, transformers, nltk, etc.)
├── README.md                   # Comprehensive architecture & evaluation documentation
├── smartlex_index.db           # Persistent SQLite database (schema, symbol table, vectors)
│
├── smartlex/                   # Core SmartLex-S Python Package
│   ├── __init__.py             # Package exports
│   ├── extractors.py           # Text extraction (PDF, DOCX, TXT) and tokenizer
│   ├── embeddings.py           # all-MiniLM-L6-v2 dense vector embedding engine
│   ├── synonyms.py             # NLTK WordNet & compiler domain synonym engine
│   ├── llm.py                  # Local Ollama client & fast extractive fallback
│   └── engine.py               # SQLite storage & 5-factor hybrid ranking engine
│
├── demo_documents/             # Compiler design demonstration corpus
│   ├── lexical_analysis.txt    # Phase 1: Tokens, Lexer, DFA/NFA, Symbol Table
│   ├── syntax_analysis.txt     # Phase 2: CFG, Parsers (LL/LR), AST, Grammar
│   └── code_optimization.txt   # Phase 3: Three-Address Code, Optimization passes
│
└── tests/
    ├── test_smartlex.py        # Core unit tests (extraction, indexing, formulas, errors)
    ├── test_gui.py             # Two-page UI regression test suite (11 test scenarios)
    └── test_fixtures.py        # 5-category baseline vs. hybrid comparative benchmark
```

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- **Python 3.10+** (tested and fully compatible with Python 3.10 through 3.14 on Windows).
- **Tkinter** (included by default in standard Windows Python distributions).

### 2. Environment Setup & Dependency Installation
Open Command Prompt or PowerShell in the project directory:

```powershell
# Create and activate virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Run Automated Verification Suites

Execute the comprehensive test suites:

```powershell
# 1. Core Engine Unit Tests (Extraction, SQLite Storage, Ranking Math)
python test_smartlex.py

# 2. Desktop UI Regression Test Suite (Two-Page Flow, Selection, Persistence)
python test_gui.py

# 3. Comparative Benchmark Evaluation (Baseline 4-Factor vs. Hybrid 5-Factor)
python test_fixtures.py
```

### 4. Launch Desktop Application

```powershell
python main.py
```

---

## 🖥️ Demonstration & Evaluation Walkthrough

Follow these steps for a complete evaluation demonstration:

1. **Launch SmartLex-S**: Run `python main.py`. Observe the dark editorial theme and active `● HYBRID RETRIEVAL ACTIVE` badge.
2. **Index Sample Documents**: Click **`⚡ Index Demo Docs`** to index the three compiler design documents into SQLite and generate dense embeddings.
3. **Keyword Search (Exact Match)**:
   - Enter `lexical analyzer tokens` and press Enter.
   - Page 2 opens: `lexical_analysis.txt` is ranked #1 with score ~`0.8960`.
   - Inspect the right panel: note the matched keywords `[lexical], [analyzer], [tokens]`, the gold-highlighted snippet, and the `SIGNALS: K=1.00 S=0.73 R=1.00 C=1.00 E=0.79` breakdown.
4. **Synonym Search**:
   - Click **`← EDIT QUERY`** to return to Page 1 with query history preserved.
   - Enter `scanner tokenization symbol table`.
   - Result: `lexical_analysis.txt` is correctly retrieved as #1 via synonym expansion and compiler domain mapping (`scanner` $\to$ `lexical analyzer`).
5. **Paraphrase / Semantic Match**:
   - Enter `eliminating unreachable program instructions`.
   - Result: `code_optimization.txt` is retrieved as #1 via dense vector similarity ($E=0.51$) despite the absence of the word `"unreachable"` in the document text.
6. **Persistence Check**:
   - Close the desktop window and relaunch `python main.py`.
   - Notice the document library badge immediately reads `LIBRARY : 3 DOCUMENTS` with all embeddings and symbol tables preserved in SQLite.

---

## 📄 License
Academic and educational use under the MIT License. SmartLex-S: Compiler-Inspired Intelligent Search.
