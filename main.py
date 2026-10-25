"""
SmartLex-S: Desktop Application
Compiler-Inspired Semantic Document Retrieval System

Two-Page Architecture:
- Page 1: Documents Library & Prominent Search Input
- Page 2: Search Results Table & Explainable Evidence Panel
Editorial Black & Muted Antique-Gold Theme with Organic Curved Line Art
"""

import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional

from smartlex.engine import SmartLexEngine
from smartlex.extractors import ExtractionError


def get_condensed_font_family() -> str:
    """Detect Agency FB or gracefully fall back to a condensed/clean sans-serif font."""
    try:
        available = set(tkfont.families())
        for candidate in ["Agency FB", "Franklin Gothic Medium", "Century Gothic", "Trebuchet MS", "Segoe UI Semibold"]:
            if candidate in available:
                return candidate
    except Exception:
        pass
    return "Segoe UI"


class SmartLexApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SmartLex-S — Semantic Document Retrieval")
        self.root.geometry("1160x760")
        self.root.minsize(1020, 680)

        # Initialize engine with persistent database in the current working directory
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "smartlex_index.db")
        self.engine = SmartLexEngine(db_path=db_path)

        # State
        self.current_query: str = ""
        self.current_results: List[Dict[str, Any]] = []
        self.active_page: str = "home"

        # Design Palette: Premium Editorial Black & Muted Antique Gold
        self.COLOR_BG = "#000000"              # Main background
        self.COLOR_SURFACE = "#0A0A09"         # Secondary surface / card
        self.COLOR_ELEVATED = "#11110F"        # Elevated surface / inputs / badges
        self.COLOR_TEXT_PRIMARY = "#F3F0E8"    # Primary warm-white text
        self.COLOR_TEXT_SECONDARY = "#B5B0A5"  # Secondary muted warm-gray text
        self.COLOR_GOLD = "#B69A5A"            # Muted antique gold accent
        self.COLOR_GOLD_HOVER = "#C9AD70"      # Hover gold
        self.COLOR_SEPARATOR = "#302A20"       # Subtle border & separator
        self.COLOR_SELECTED_ROW = "#211D15"    # Selected row background
        self.COLOR_HIGHLIGHT_BG = "#382D16"    # Matched keywords background
        self.COLOR_HIGHLIGHT_FG = "#F3E2B8"    # Matched keywords foreground
        self.COLOR_WARN = "#D97706"            # Warm warning amber

        # Typography
        self.FONT_AGENCY = get_condensed_font_family()
        self.FONT_READING = "Segoe UI" if "Segoe UI" in set(tkfont.families()) else self.FONT_AGENCY
        self.FONT_CODE = "Consolas" if "Consolas" in set(tkfont.families()) else "Courier"

        # Apply root background
        self.root.configure(bg=self.COLOR_BG)

        # Setup ttk styles with dark clam theme
        self._setup_styles()

        # Build Master UI Container & Pages
        self._build_master_container()

        # Populate initial document stats and show home page
        self.refresh_documents_list()
        self.show_page_home()

    def _setup_styles(self):
        """Configure ttk styles in black, warm-white, and antique-gold."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Treeview Styling
        style.configure(
            "Treeview",
            background=self.COLOR_SURFACE,
            foreground=self.COLOR_TEXT_PRIMARY,
            fieldbackground=self.COLOR_SURFACE,
            rowheight=30,
            font=(self.FONT_AGENCY, 10),
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "Treeview.Heading",
            background="#12100A",
            foreground=self.COLOR_GOLD,
            font=(self.FONT_AGENCY, 11, "bold"),
            relief="flat",
            borderwidth=1,
            bordercolor=self.COLOR_SEPARATOR
        )
        style.map(
            "Treeview",
            background=[("selected", self.COLOR_SELECTED_ROW)],
            foreground=[("selected", "#FFFFFF")]
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#1A1710")],
            foreground=[("active", self.COLOR_GOLD_HOVER)]
        )

        # Scrollbars
        style.configure(
            "Vertical.TScrollbar",
            background="#12100A",
            troughcolor="#050505",
            bordercolor=self.COLOR_SEPARATOR,
            arrowcolor=self.COLOR_GOLD,
            relief="flat"
        )
        style.configure(
            "Horizontal.TScrollbar",
            background="#12100A",
            troughcolor="#050505",
            bordercolor=self.COLOR_SEPARATOR,
            arrowcolor=self.COLOR_GOLD,
            relief="flat"
        )

        # Primary Gold Action Button (SEARCH)
        style.configure(
            "GoldAction.TButton",
            font=(self.FONT_AGENCY, 12, "bold"),
            background=self.COLOR_GOLD,
            foreground="#000000",
            bordercolor=self.COLOR_GOLD,
            focuscolor="none",
            padding=(18, 6)
        )
        style.map(
            "GoldAction.TButton",
            background=[("active", self.COLOR_GOLD_HOVER), ("pressed", "#9E8345")],
            foreground=[("active", "#000000")]
        )

        # Secondary Dark Action Button
        style.configure(
            "DarkTool.TButton",
            font=(self.FONT_AGENCY, 10, "bold"),
            background=self.COLOR_ELEVATED,
            foreground=self.COLOR_TEXT_PRIMARY,
            bordercolor=self.COLOR_SEPARATOR,
            focuscolor="none",
            padding=(10, 5)
        )
        style.map(
            "DarkTool.TButton",
            background=[("active", "#1D1912"), ("pressed", "#0A0805")],
            foreground=[("active", "#FFFFFF")],
            bordercolor=[("active", self.COLOR_GOLD)]
        )

        # Nav Back Button
        style.configure(
            "NavBack.TButton",
            font=(self.FONT_AGENCY, 11, "bold"),
            background="#16130E",
            foreground=self.COLOR_GOLD,
            bordercolor=self.COLOR_GOLD,
            focuscolor="none",
            padding=(12, 5)
        )
        style.map(
            "NavBack.TButton",
            background=[("active", "#251F14"), ("pressed", "#0F0D08")],
            foreground=[("active", self.COLOR_GOLD_HOVER)],
            bordercolor=[("active", self.COLOR_GOLD_HOVER)]
        )

    def _build_master_container(self):
        """Construct the master background canvas and page frames."""
        # Full-window background canvas for organic antique-gold curves
        self.bg_canvas = tk.Canvas(
            self.root, 
            bg=self.COLOR_BG, 
            highlightthickness=0, 
            bd=0
        )
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_canvas.bind("<Configure>", self._draw_background_curves)

        # Master page container sitting above background canvas
        self.container = tk.Frame(self.root, bg=self.COLOR_BG)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Build Page 1: Documents & Search
        self.page_home = tk.Frame(self.container, bg=self.COLOR_BG)
        self._build_page_home()

        # Build Page 2: Results & Explainable Evidence
        self.page_results = tk.Frame(self.container, bg=self.COLOR_BG)
        self._build_page_results()

    def _draw_background_curves(self, event=None):
        """
        Draw elegant, thin, flowing organic curves in muted antique gold across the background.
        Asymmetric, low-contrast, non-interfering, scales with the window.
        """
        self.bg_canvas.delete("curve")
        w = self.bg_canvas.winfo_width()
        h = self.bg_canvas.winfo_height()
        if w <= 10 or h <= 10:
            return

        # Curve 1: Top header graceful sweep (low-contrast antique gold #272115)
        self.bg_canvas.create_line(
            -30, h * 0.10,
            w * 0.22, h * 0.04,
            w * 0.52, h * 0.14,
            w * 0.82, h * 0.06,
            w + 40, h * 0.12,
            smooth=True, fill="#272115", width=1, tags="curve"
        )

        # Curve 2: Diagonal soft counter-wave
        self.bg_canvas.create_line(
            -20, h * 0.35,
            w * 0.30, h * 0.52,
            w * 0.65, h * 0.28,
            w * 0.90, h * 0.45,
            w + 30, h * 0.32,
            smooth=True, fill="#1D180E", width=1, tags="curve"
        )

        # Curve 3: Lower subtle contour
        self.bg_canvas.create_line(
            -40, h * 0.82,
            w * 0.18, h * 0.68,
            w * 0.48, h * 0.88,
            w * 0.78, h * 0.74,
            w + 20, h * 0.86,
            smooth=True, fill="#221C11", width=1, tags="curve"
        )

        # Ensure background canvas lines stay behind all container elements
        self.bg_canvas.tag_lower("curve")

    # =========================================================================
    # PAGE 1: DOCUMENTS AND SEARCH (HOME SCREEN)
    # =========================================================================
    def _build_page_home(self):
        """Build Page 1: Header, Document Library Management, and Search Section."""
        # Top Header Bar
        p1_header = tk.Frame(self.page_home, bg=self.COLOR_BG, padx=28, pady=20)
        p1_header.pack(fill=tk.X, side=tk.TOP)

        p1_title_box = tk.Frame(p1_header, bg=self.COLOR_BG)
        p1_title_box.pack(side=tk.LEFT, anchor="w")

        p1_wordmark = tk.Label(
            p1_title_box,
            text="SMARTLEX-S",
            font=(self.FONT_AGENCY, 24, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_BG
        )
        p1_wordmark.pack(side=tk.LEFT, anchor="w")

        p1_div = tk.Label(
            p1_title_box,
            text="  |  ",
            font=(self.FONT_AGENCY, 16),
            fg=self.COLOR_SEPARATOR,
            bg=self.COLOR_BG
        )
        p1_div.pack(side=tk.LEFT)

        p1_sub = tk.Label(
            p1_title_box,
            text="Compiler-Inspired Semantic Document Retrieval",
            font=(self.FONT_READING, 10),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG
        )
        p1_sub.pack(side=tk.LEFT, anchor="w")

        # Right status badge on header
        p1_right_box = tk.Frame(p1_header, bg=self.COLOR_BG)
        p1_right_box.pack(side=tk.RIGHT, anchor="e")

        self.home_doc_badge = tk.Label(
            p1_right_box,
            text="LIBRARY : 0 DOCUMENTS",
            font=(self.FONT_AGENCY, 10, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_ELEVATED,
            padx=12,
            pady=5,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            bd=0
        )
        self.home_doc_badge.pack(side=tk.RIGHT)

        # Subtle gold divider
        p1_sep = tk.Frame(self.page_home, height=1, bg=self.COLOR_SEPARATOR)
        p1_sep.pack(fill=tk.X, padx=28, pady=(0, 16))

        # Main Scrollable / Spacious Body Frame
        home_body = tk.Frame(self.page_home, bg=self.COLOR_BG, padx=28)
        home_body.pack(fill=tk.BOTH, expand=True)

        # --- SECTION A: DOCUMENT MANAGEMENT ("DOCUMENT LIBRARY") ---
        lib_card = tk.Frame(
            home_body,
            bg=self.COLOR_SURFACE,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            padx=20,
            pady=16
        )
        lib_card.pack(fill=tk.X, pady=(0, 16))

        lib_header_row = tk.Frame(lib_card, bg=self.COLOR_SURFACE)
        lib_header_row.pack(fill=tk.X, pady=(0, 4))

        lib_title = tk.Label(
            lib_header_row,
            text="DOCUMENT LIBRARY",
            font=(self.FONT_AGENCY, 13, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_SURFACE
        )
        lib_title.pack(side=tk.LEFT)

        self.lib_count_caption = tk.Label(
            lib_header_row,
            text="0 Documents Indexed",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE
        )
        self.lib_count_caption.pack(side=tk.RIGHT)

        lib_desc = tk.Label(
            lib_card,
            text="Import text, PDF, or Word documents into the persistent SQLite index. Extracted text is tokenized into compiler symbol tables.",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE,
            anchor="w"
        )
        lib_desc.pack(fill=tk.X, pady=(0, 12))

        # Document Action Toolbar
        lib_toolbar = tk.Frame(lib_card, bg=self.COLOR_SURFACE)
        lib_toolbar.pack(fill=tk.X, pady=(0, 10))

        add_btn = ttk.Button(
            lib_toolbar,
            text="+ Add Documents",
            style="DarkTool.TButton",
            command=self.add_documents
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 6))

        demo_btn = ttk.Button(
            lib_toolbar,
            text="⚡ Index Demo Docs",
            style="DarkTool.TButton",
            command=self.load_demo_documents
        )
        demo_btn.pack(side=tk.LEFT, padx=(0, 6))

        refresh_btn = ttk.Button(
            lib_toolbar,
            text="🔄 Refresh",
            style="DarkTool.TButton",
            command=self.refresh_documents_list
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 6))

        clear_btn = ttk.Button(
            lib_toolbar,
            text="🗑️ Clear Index",
            style="DarkTool.TButton",
            command=self.clear_index_dialog
        )
        clear_btn.pack(side=tk.LEFT)

        # Operational status label in library
        self.home_status_lbl = tk.Label(
            lib_card,
            text="Status: Ready. Index demo documents or import your files to get started.",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE,
            anchor="w"
        )
        self.home_status_lbl.pack(fill=tk.X, pady=(4, 8))

        # Compact preview list of indexed documents
        self.home_docs_preview_box = tk.Frame(
            lib_card, 
            bg=self.COLOR_ELEVATED, 
            highlightbackground=self.COLOR_SEPARATOR, 
            highlightthickness=1,
            padx=12,
            pady=8
        )
        self.home_docs_preview_box.pack(fill=tk.X)

        self.home_docs_preview_lbl = tk.Label(
            self.home_docs_preview_box,
            text="No documents currently indexed.",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_ELEVATED,
            anchor="w",
            justify="left"
        )
        self.home_docs_preview_lbl.pack(fill=tk.X)

        # --- SECTION B: SEARCH SECTION ("FIND RELEVANT DOCUMENTS") ---
        search_card = tk.Frame(
            home_body,
            bg=self.COLOR_SURFACE,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        search_card.pack(fill=tk.X, pady=(0, 16))

        search_heading = tk.Label(
            search_card,
            text="FIND RELEVANT DOCUMENTS",
            font=(self.FONT_AGENCY, 16, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_SURFACE,
            anchor="w"
        )
        search_heading.pack(fill=tk.X)

        search_subheading = tk.Label(
            search_card,
            text="Search your indexed documents and inspect the evidence behind every result.",
            font=(self.FONT_READING, 10),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE,
            anchor="w"
        )
        search_subheading.pack(fill=tk.X, pady=(2, 14))

        # Query Input Box
        input_container = tk.Frame(search_card, bg=self.COLOR_SURFACE)
        input_container.pack(fill=tk.X, pady=(0, 12))

        self.query_var = tk.StringVar()
        self.query_entry = tk.Entry(
            input_container,
            textvariable=self.query_var,
            font=(self.FONT_READING, 11),
            bg=self.COLOR_ELEVATED,
            fg=self.COLOR_TEXT_PRIMARY,
            insertbackground=self.COLOR_GOLD,
            selectbackground=self.COLOR_HIGHLIGHT_BG,
            selectforeground=self.COLOR_TEXT_PRIMARY,
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightcolor=self.COLOR_GOLD
        )
        self.query_entry.pack(fill=tk.X, ipady=7, padx=(0, 0))
        self.query_entry.bind("<Return>", lambda event: self.perform_search())

        # Inline validation feedback label
        self.search_validation_lbl = tk.Label(
            search_card,
            text="",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_WARN,
            bg=self.COLOR_SURFACE,
            anchor="w"
        )
        self.search_validation_lbl.pack(fill=tk.X, pady=(0, 6))

        # Search Actions Row
        action_row = tk.Frame(search_card, bg=self.COLOR_SURFACE)
        action_row.pack(fill=tk.X)

        search_btn = ttk.Button(
            action_row,
            text="SEARCH DOCUMENTS",
            style="GoldAction.TButton",
            command=self.perform_search
        )
        search_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_search_btn = ttk.Button(
            action_row,
            text="CLEAR QUERY",
            style="DarkTool.TButton",
            command=self.clear_search
        )
        clear_search_btn.pack(side=tk.LEFT)

        # Example query prompt pills
        example_lbl = tk.Label(
            action_row,
            text="Try: 'lexical analyzer tokens'  |  'syntax parsing AST'  |  'intermediate code optimization'",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE
        )
        example_lbl.pack(side=tk.RIGHT)

        # --- SECTION C: READINESS & FORMULA FOOTER ---
        footer_card = tk.Frame(
            home_body,
            bg=self.COLOR_BG,
            pady=10
        )
        footer_card.pack(fill=tk.X, side=tk.BOTTOM)

        self.home_readiness_lbl = tk.Label(
            footer_card,
            text="INDEX STATUS : READY — 3 DOCUMENTS STORED IN SQLITE",
            font=(self.FONT_AGENCY, 10),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG
        )
        self.home_readiness_lbl.pack(side=tk.LEFT)

        formula_preview_lbl = tk.Label(
            footer_card,
            text="Transparent 4-Factor Ranking Formula: FinalScore = 0.40K + 0.25S + 0.20R + 0.15C",
            font=(self.FONT_AGENCY, 10),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_BG
        )
        formula_preview_lbl.pack(side=tk.RIGHT)

    # =========================================================================
    # PAGE 2: SEARCH RESULTS AND EXPLAINABLE EVIDENCE
    # =========================================================================
    def _build_page_results(self):
        """Build Page 2: Results-page header, 2-column layout (52% left, 48% right)."""
        # --- A. RESULTS-PAGE HEADER ---
        p2_header = tk.Frame(self.page_results, bg=self.COLOR_BG, padx=24, pady=14)
        p2_header.pack(fill=tk.X, side=tk.TOP)

        p2_left_header = tk.Frame(p2_header, bg=self.COLOR_BG)
        p2_left_header.pack(side=tk.LEFT, anchor="w")

        p2_wordmark = tk.Label(
            p2_left_header,
            text="SMARTLEX-S",
            font=(self.FONT_AGENCY, 20, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_BG
        )
        p2_wordmark.pack(side=tk.LEFT, anchor="w")

        p2_res_tag = tk.Label(
            p2_left_header,
            text="SEARCH RESULTS",
            font=(self.FONT_AGENCY, 9, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_ELEVATED,
            padx=8,
            pady=3,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            bd=0
        )
        p2_res_tag.pack(side=tk.LEFT, padx=12)

        self.p2_query_display = tk.Label(
            p2_left_header,
            text="QUERY: \"...\"",
            font=(self.FONT_READING, 10, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_BG
        )
        self.p2_query_display.pack(side=tk.LEFT)

        # Right Header Controls
        p2_right_header = tk.Frame(p2_header, bg=self.COLOR_BG)
        p2_right_header.pack(side=tk.RIGHT, anchor="e")

        self.p2_matches_badge = tk.Label(
            p2_right_header,
            text="0 MATCHES",
            font=(self.FONT_AGENCY, 10, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_ELEVATED,
            padx=10,
            pady=4,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            bd=0
        )
        self.p2_matches_badge.pack(side=tk.LEFT, padx=(0, 10))

        # Explicit EDIT QUERY button to return to Page 1
        edit_query_btn = ttk.Button(
            p2_right_header,
            text="← EDIT QUERY",
            style="NavBack.TButton",
            command=self.show_page_home
        )
        edit_query_btn.pack(side=tk.LEFT)

        # Subtle gold divider
        p2_sep = tk.Frame(self.page_results, height=1, bg=self.COLOR_SEPARATOR)
        p2_sep.pack(fill=tk.X, padx=24, pady=(0, 10))

        # --- B. TWO-COLUMN RESPONSIVE LAYOUT ---
        # 52% Left, 48% Right
        p2_content = tk.Frame(self.page_results, bg=self.COLOR_BG, padx=24, pady=4)
        p2_content.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        p2_content.grid_columnconfigure(0, weight=52, uniform="results_cols")
        p2_content.grid_columnconfigure(1, weight=48, uniform="results_cols")
        p2_content.grid_rowconfigure(0, weight=1)

        # === LEFT PANEL: MATCHED DOCUMENTS (TABLE) ===
        self.p2_left_panel = tk.Frame(
            p2_content,
            bg=self.COLOR_SURFACE,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            padx=12,
            pady=12
        )
        self.p2_left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        left_title_row = tk.Frame(self.p2_left_panel, bg=self.COLOR_SURFACE)
        left_title_row.pack(fill=tk.X, pady=(0, 8))

        left_title = tk.Label(
            left_title_row,
            text="MATCHED DOCUMENTS",
            font=(self.FONT_AGENCY, 12, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_SURFACE
        )
        left_title.pack(side=tk.LEFT)

        self.p2_table_count_lbl = tk.Label(
            left_title_row,
            text="RANKED BY COMPILER HEURISTIC FORMULA",
            font=(self.FONT_AGENCY, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE
        )
        self.p2_table_count_lbl.pack(side=tk.RIGHT)

        # Table & Empty State Stack Container
        self.table_stack_frame = tk.Frame(self.p2_left_panel, bg=self.COLOR_SURFACE)
        self.table_stack_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview with Scrollbars
        self.tree_container = tk.Frame(self.table_stack_frame, bg=self.COLOR_SURFACE)
        self.tree_container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            self.tree_container,
            columns=("rank", "name", "type", "final", "k", "s", "r", "c"),
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("rank", text="RANK")
        self.tree.heading("name", text="DOCUMENT FILE")
        self.tree.heading("type", text="TYPE")
        self.tree.heading("final", text="SCORE")
        self.tree.heading("k", text="K (COV)")
        self.tree.heading("s", text="S (SIM)")
        self.tree.heading("r", text="R (REL)")
        self.tree.heading("c", text="C (SENT)")

        self.tree.column("rank", width=46, anchor="center")
        self.tree.column("name", width=190, anchor="w")
        self.tree.column("type", width=52, anchor="center")
        self.tree.column("final", width=75, anchor="center")
        self.tree.column("k", width=58, anchor="center")
        self.tree.column("s", width=58, anchor="center")
        self.tree.column("r", width=58, anchor="center")
        self.tree.column("c", width=58, anchor="center")

        tree_y_scroll = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        tree_x_scroll = ttk.Scrollbar(self.tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_y_scroll.set, xscrollcommand=tree_x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_y_scroll.grid(row=0, column=1, sticky="ns")
        tree_x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_result_selected)

        # Empty State Card (Hidden by default, shown when 0 results)
        self.empty_state_frame = tk.Frame(self.table_stack_frame, bg=self.COLOR_ELEVATED, padx=20, pady=30)
        
        empty_icon = tk.Label(
            self.empty_state_frame,
            text="🔍",
            font=(self.FONT_AGENCY, 24),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_ELEVATED
        )
        empty_icon.pack(pady=(0, 6))

        empty_heading = tk.Label(
            self.empty_state_frame,
            text="No relevant documents found.",
            font=(self.FONT_AGENCY, 14, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_ELEVATED
        )
        empty_heading.pack(pady=(0, 6))

        empty_desc = tk.Label(
            self.empty_state_frame,
            text="No indexed documents matched your query terms.\nTry using broader keywords, checking for typos, or adding more documents to the library.",
            font=(self.FONT_READING, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_ELEVATED,
            justify="center"
        )
        empty_desc.pack(pady=(0, 16))

        empty_back_btn = ttk.Button(
            self.empty_state_frame,
            text="← EDIT QUERY",
            style="GoldAction.TButton",
            command=self.show_page_home
        )
        empty_back_btn.pack()

        # === RIGHT PANEL: EVIDENCE & SCORE BREAKDOWN ===
        self.p2_right_panel = tk.Frame(
            p2_content,
            bg=self.COLOR_SURFACE,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            padx=14,
            pady=12
        )
        self.p2_right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        right_title_row = tk.Frame(self.p2_right_panel, bg=self.COLOR_SURFACE)
        right_title_row.pack(fill=tk.X, pady=(0, 8))

        evidence_title = tk.Label(
            right_title_row,
            text="EVIDENCE & SCORE BREAKDOWN",
            font=(self.FONT_AGENCY, 12, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_SURFACE
        )
        evidence_title.pack(side=tk.LEFT)

        formula_tag = tk.Label(
            right_title_row,
            text="0.40K + 0.25S + 0.20R + 0.15C",
            font=(self.FONT_AGENCY, 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_SURFACE
        )
        formula_tag.pack(side=tk.RIGHT)

        # Selected Result Metadata Card
        self.res_meta_card = tk.Frame(
            self.p2_right_panel,
            bg=self.COLOR_ELEVATED,
            highlightbackground=self.COLOR_SEPARATOR,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        self.res_meta_card.pack(fill=tk.X, pady=(0, 10))

        self.res_doc_name = tk.Label(
            self.res_meta_card,
            text="Select a document to inspect evidence",
            font=(self.FONT_AGENCY, 13, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_ELEVATED,
            anchor="w"
        )
        self.res_doc_name.pack(fill=tk.X)

        self.res_score_lbl = tk.Label(
            self.res_meta_card,
            text="FINAL SCORE : —",
            font=(self.FONT_AGENCY, 12, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_ELEVATED,
            anchor="w"
        )
        self.res_score_lbl.pack(fill=tk.X, pady=(2, 4))

        # Matched Keywords Container
        kw_box = tk.Frame(self.res_meta_card, bg=self.COLOR_ELEVATED)
        kw_box.pack(fill=tk.X)

        kw_lbl_tag = tk.Label(
            kw_box,
            text="MATCHED KEYWORDS :",
            font=(self.FONT_AGENCY, 9, "bold"),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_ELEVATED
        )
        kw_lbl_tag.pack(side=tk.LEFT, padx=(0, 6))

        self.res_keywords_lbl = tk.Label(
            kw_box,
            text="None",
            font=(self.FONT_READING, 9, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_ELEVATED,
            anchor="w"
        )
        self.res_keywords_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Snippet Box
        snippet_header = tk.Frame(self.p2_right_panel, bg=self.COLOR_SURFACE)
        snippet_header.pack(fill=tk.X, pady=(2, 4))

        snippet_lbl = tk.Label(
            snippet_header,
            text="RELEVANT TEXT SNIPPET (BEST-MATCHING SENTENCE):",
            font=(self.FONT_AGENCY, 10, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_SURFACE
        )
        snippet_lbl.pack(side=tk.LEFT)

        snippet_container = tk.Frame(self.p2_right_panel, bg=self.COLOR_SURFACE)
        snippet_container.pack(fill=tk.X, pady=(0, 10))

        self.snippet_text = tk.Text(
            snippet_container,
            height=5,
            font=(self.FONT_READING, 9),
            wrap="word",
            relief="flat",
            bd=0,
            bg="#060503",
            fg=self.COLOR_TEXT_PRIMARY,
            insertbackground=self.COLOR_GOLD,
            highlightthickness=1,
            highlightbackground=self.COLOR_SEPARATOR,
            padx=10,
            pady=8
        )
        self.snippet_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        snippet_scroll = ttk.Scrollbar(snippet_container, orient=tk.VERTICAL, command=self.snippet_text.yview)
        snippet_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.snippet_text.configure(yscrollcommand=snippet_scroll.set)

        self.snippet_text.tag_configure(
            "highlight",
            background=self.COLOR_HIGHLIGHT_BG,
            foreground=self.COLOR_HIGHLIGHT_FG,
            font=(self.FONT_READING, 9, "bold")
        )
        self.snippet_text.configure(state="disabled")

        # Score Explanation Box
        explanation_header = tk.Frame(self.p2_right_panel, bg=self.COLOR_SURFACE)
        explanation_header.pack(fill=tk.X, pady=(2, 4))

        explanation_lbl = tk.Label(
            explanation_header,
            text="TRANSPARENT SCORING BREAKDOWN:",
            font=(self.FONT_AGENCY, 10, "bold"),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_SURFACE
        )
        explanation_lbl.pack(side=tk.LEFT)

        explanation_container = tk.Frame(self.p2_right_panel, bg=self.COLOR_SURFACE)
        explanation_container.pack(fill=tk.BOTH, expand=True)

        self.explanation_text = tk.Text(
            explanation_container,
            height=9,
            font=(self.FONT_CODE, 9),
            wrap="word",
            relief="flat",
            bd=0,
            bg="#060503",
            fg=self.COLOR_TEXT_PRIMARY,
            insertbackground=self.COLOR_GOLD,
            highlightthickness=1,
            highlightbackground=self.COLOR_SEPARATOR,
            padx=10,
            pady=8
        )
        self.explanation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        exp_scroll = ttk.Scrollbar(explanation_container, orient=tk.VERTICAL, command=self.explanation_text.yview)
        exp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.explanation_text.configure(yscrollcommand=exp_scroll.set)
        self.explanation_text.configure(state="disabled")

        # Bottom Status Bar on Page 2
        p2_status_bar = tk.Frame(self.page_results, bg=self.COLOR_BG, padx=24, pady=6)
        p2_status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        p2_status_sep = tk.Frame(self.page_results, height=1, bg=self.COLOR_SEPARATOR)
        p2_status_sep.pack(fill=tk.X, side=tk.BOTTOM)

        self.p2_status_lbl = tk.Label(
            p2_status_bar,
            text="Viewing results. Click '← EDIT QUERY' to modify search.",
            font=(self.FONT_AGENCY, 10),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG
        )
        self.p2_status_lbl.pack(side=tk.LEFT)

        p2_footer_info = tk.Label(
            p2_status_bar,
            text="SmartLex-S | Editorial Semantic Engine",
            font=(self.FONT_AGENCY, 10),
            fg=self.COLOR_GOLD,
            bg=self.COLOR_BG
        )
        p2_footer_info.pack(side=tk.RIGHT)

    # =========================================================================
    # PAGE NAVIGATION & STATE PRESERVATION
    # =========================================================================
    def show_page_home(self):
        """Navigate to Page 1 (Documents & Search Home). Preserves query and index state."""
        self.active_page = "home"
        self.page_results.pack_forget()
        self.page_home.pack(fill=tk.BOTH, expand=True)

        # Restore previous query into search input and focus it for editing
        self.query_var.set(self.current_query)
        self.search_validation_lbl.config(text="")
        self.query_entry.focus()
        if self.current_query:
            self.query_entry.select_range(0, tk.END)

        # Update library count
        self.refresh_documents_list()

    def show_page_results(self):
        """Navigate to Page 2 (Search Results & Evidence)."""
        self.active_page = "results"
        self.page_home.pack_forget()
        self.page_results.pack(fill=tk.BOTH, expand=True)

        # Update query display header
        display_q = self.current_query if len(self.current_query) <= 35 else self.current_query[:32] + "..."
        self.p2_query_display.config(text=f"QUERY: \"{display_q}\"")

        # Update matches badge
        match_count = len(self.current_results)
        self.p2_matches_badge.config(text=f"{match_count} {'MATCH' if match_count == 1 else 'MATCHES'} FOUND")

        # Render results in table or show empty state
        if match_count == 0:
            self.tree_container.pack_forget()
            self.empty_state_frame.pack(fill=tk.BOTH, expand=True)
            self._clear_evidence_panel()
            self.res_doc_name.config(text="No Relevant Documents Found")
            self.res_score_lbl.config(text="FINAL SCORE : 0.0000")
            self.res_keywords_lbl.config(text="None")
            self._update_text_widget(
                self.snippet_text,
                "No matching sentence found in the document library for this query."
            )
            self._update_text_widget(
                self.explanation_text,
                "Zero term matches detected in the document symbol tables.\nTry refining query terms or indexing additional documents."
            )
        else:
            self.empty_state_frame.pack_forget()
            self.tree_container.pack(fill=tk.BOTH, expand=True)

            # Clear and repopulate tree
            for item in self.tree.get_children():
                self.tree.delete(item)

            for rank, res in enumerate(self.current_results, start=1):
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(rank - 1),
                    values=(
                        f"#{rank}",
                        res["filename"],
                        res["file_type"],
                        f"{res['final_score']:.4f}",
                        f"{res['score_k']:.2f}",
                        f"{res['score_s']:.2f}",
                        f"{res['score_r']:.2f}",
                        f"{res['score_c']:.2f}"
                    )
                )

            # Automatically select the first ranked result
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
            self.on_result_selected(None)

    # =========================================================================
    # DOCUMENT MANAGEMENT LOGIC
    # =========================================================================
    def refresh_documents_list(self):
        """Fetch all documents in the SQLite store and update library status."""
        docs = self.engine.get_indexed_documents()
        total_docs = len(docs)

        # Update badges
        plural = "DOCUMENT" if total_docs == 1 else "DOCUMENTS"
        self.home_doc_badge.config(text=f"LIBRARY : {total_docs} {plural}")
        self.lib_count_caption.config(text=f"{total_docs} Documents Indexed")

        if total_docs == 0:
            self.home_status_lbl.config(
                text="Status: Your document library is empty. Click 'Index Demo Docs' or 'Add Documents' to begin.",
                fg=self.COLOR_TEXT_SECONDARY
            )
            self.home_docs_preview_lbl.config(text="No documents currently indexed in SQLite.")
            self.home_readiness_lbl.config(
                text="INDEX STATUS : EMPTY — ADD DOCUMENTS TO ENABLE RETRIEVAL",
                fg=self.COLOR_WARN
            )
        else:
            self.home_status_lbl.config(
                text=f"Status: {total_docs} document(s) indexed and ready in SQLite.",
                fg=self.COLOR_TEXT_SECONDARY
            )
            preview_items = [f"• {d['filename']}  [{d['file_type']}, {d['token_count']} tokens]" for d in docs[:4]]
            if len(docs) > 4:
                preview_items.append(f"...and {len(docs) - 4} more documents.")
            self.home_docs_preview_lbl.config(text="\n".join(preview_items))
            self.home_readiness_lbl.config(
                text=f"INDEX STATUS : READY — {total_docs} DOCUMENTS STORED IN SQLITE",
                fg=self.COLOR_TEXT_SECONDARY
            )

    def add_documents(self):
        """Allow user to select and import multiple PDF, DOCX, and TXT files."""
        filetypes = [
            ("Supported Documents (*.txt, *.pdf, *.docx)", "*.txt;*.pdf;*.docx"),
            ("Text Files (*.txt)", "*.txt"),
            ("PDF Files (*.pdf)", "*.pdf"),
            ("Word Documents (*.docx)", "*.docx"),
            ("All Files (*.*)", "*.*")
        ]
        chosen_files = filedialog.askopenfilenames(
            title="Select Documents to Index in SmartLex-S",
            filetypes=filetypes
        )
        if not chosen_files:
            return

        success_count = 0
        error_messages = []

        self.home_status_lbl.config(text=f"Indexing {len(chosen_files)} document(s)...")

        for fpath in chosen_files:
            try:
                self.engine.index_document(fpath)
                success_count += 1
            except ExtractionError as ee:
                error_messages.append(f"{os.path.basename(fpath)}: {str(ee)}")
            except Exception as e:
                error_messages.append(f"{os.path.basename(fpath)}: Unexpected error: {str(e)}")

        self.refresh_documents_list()

        if error_messages:
            msg = (
                f"Indexed {success_count} of {len(chosen_files)} files.\n\n"
                f"The following issues occurred:\n" + "\n".join(f"• {m}" for m in error_messages[:5])
            )
            if len(error_messages) > 5:
                msg += f"\n...and {len(error_messages) - 5} more."
            messagebox.showwarning("Document Import Notice", msg)
            self.home_status_lbl.config(
                text=f"Import completed with {len(error_messages)} issue(s).",
                fg=self.COLOR_WARN
            )
        else:
            self.home_status_lbl.config(
                text=f"Successfully indexed {success_count} document(s).",
                fg=self.COLOR_TEXT_PRIMARY
            )

    def load_demo_documents(self):
        """Automatically index the 3 sample demonstration documents."""
        base_dir = os.path.abspath(os.path.dirname(__file__))
        demo_dir = os.path.join(base_dir, "demo_documents")

        if not os.path.exists(demo_dir):
            messagebox.showerror("Error", f"Demo directory not found: {demo_dir}")
            return

        demo_files = [
            os.path.join(demo_dir, "lexical_analysis.txt"),
            os.path.join(demo_dir, "syntax_analysis.txt"),
            os.path.join(demo_dir, "code_optimization.txt")
        ]

        indexed_any = False
        for df in demo_files:
            if os.path.exists(df):
                try:
                    self.engine.index_document(df)
                    indexed_any = True
                except Exception as e:
                    messagebox.showerror("Error", f"Could not index demo file {os.path.basename(df)}: {str(e)}")

        if indexed_any:
            self.refresh_documents_list()
            self.home_status_lbl.config(
                text="Three sample compiler documents indexed successfully! Ready to search.",
                fg=self.COLOR_TEXT_PRIMARY
            )
            messagebox.showinfo(
                "Demo Documents Ready",
                "Three sample documents have been indexed:\n"
                "1. Lexical Analysis (Phase 1: tokens, scanner, symbol table)\n"
                "2. Syntax Analysis (Phase 2: parsing, CFG, AST)\n"
                "3. Code Optimization (Phase 3: TAC, basic blocks, peephole)\n\n"
                "Enter a search query below to retrieve results and inspect evidence."
            )
        else:
            messagebox.showwarning("Notice", "No demo text files were found to index.")

    def clear_index_dialog(self):
        """Ask confirmation and clear the SQLite index."""
        if messagebox.askyesno(
            "Confirm Clear Index", 
            "Are you sure you want to delete all indexed documents from the persistent SQLite database?"
        ):
            self.engine.clear_index()
            self.refresh_documents_list()
            self.home_status_lbl.config(
                text="All indexed documents have been cleared from the database.",
                fg=self.COLOR_TEXT_SECONDARY
            )

    # =========================================================================
    # SEARCH & RETRIEVAL LOGIC
    # =========================================================================
    def perform_search(self):
        """Validate query, execute 4-part ranking retrieval pipeline, and navigate to Page 2."""
        query = self.query_var.get().strip()
        if not query:
<<<<<<< HEAD
            self.search_validation_lbl.config(text="[!] Please enter search terms to retrieve documents.")
=======
            self.search_validation_lbl.config(text="⚠ Please enter search terms to retrieve documents.")
>>>>>>> origin/main
            self.query_entry.focus()
            return

        self.search_validation_lbl.config(text="")

        # Check if index has documents
        docs = self.engine.get_indexed_documents()
        if not docs:
            messagebox.showinfo(
                "No Documents Indexed",
                "Your document library is currently empty.\nPlease click 'Index Demo Docs' or 'Add Documents' before searching."
            )
            self.query_entry.focus()
            return

        # Execute existing retrieval and ranking pipeline
        results = self.engine.search(query)

        # Update application state
        self.current_query = query
        self.current_results = results

        # Navigate to Page 2 (Results & Evidence)
        self.show_page_results()

    def clear_search(self):
        """Clear query entry and validation message."""
        self.query_var.set("")
        self.current_query = ""
        self.search_validation_lbl.config(text="")
        self.query_entry.focus()

    # =========================================================================
    # RESULTS EVIDENCE DISPLAY
    # =========================================================================
    def on_result_selected(self, event):
        """Handle treeview row selection to update the evidence and explanation panel."""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]

        try:
            res_idx = int(item_id)
            if res_idx >= len(self.current_results):
                return
            res = self.current_results[res_idx]
        except ValueError:
            return

        # Update metadata card
        matched_str = ", ".join(f"[{kw}]" for kw in res["matched_keywords"]) if res["matched_keywords"] else "None"
        self.res_doc_name.config(
            text=f"Rank #{res_idx + 1} — {res['filename']}  [{res['file_type']}]"
        )
        self.res_score_lbl.config(
            text=f"FINAL SCORE : {res['final_score']:.4f}  ({res['final_score']*100:.1f}%)"
        )
        self.res_keywords_lbl.config(text=matched_str)

        # Update Snippet with query keyword highlighting
        snippet_content = res["snippet"] if res["snippet"] else "No specific sentence matched."
        self._update_text_widget(self.snippet_text, snippet_content)
        self._highlight_keywords(self.snippet_text, res["matched_keywords"])

        # Update Explanation
        self._update_text_widget(self.explanation_text, res["explanation"])

    def _highlight_keywords(self, text_widget: tk.Text, keywords: List[str]):
        """Highlight matched query keywords in the text widget with warm gold."""
        if not keywords:
            return
        text_content = text_widget.get("1.0", tk.END).lower()
        for kw in keywords:
            kw_clean = kw.lower()
            start_pos = 0
            while True:
                idx = text_content.find(kw_clean, start_pos)
                if idx == -1:
                    break
                start_index = f"1.0 + {idx} chars"
                end_index = f"1.0 + {idx + len(kw_clean)} chars"
                text_widget.tag_add("highlight", start_index, end_index)
                start_pos = idx + len(kw_clean)

    def _update_text_widget(self, widget: tk.Text, content: str):
        """Safely update disabled text widget content."""
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="disabled")

    def _clear_evidence_panel(self):
        """Reset the evidence text widgets."""
        self.res_doc_name.config(text="No document selected")
        self.res_score_lbl.config(text="FINAL SCORE : —")
        self.res_keywords_lbl.config(text="None")
        self._update_text_widget(self.snippet_text, "")
        self._update_text_widget(self.explanation_text, "")


def main():
    root = tk.Tk()
    app = SmartLexApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
