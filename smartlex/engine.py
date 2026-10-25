"""
SmartLex-S Core Retrieval Engine.
Implements SQLite persistent indexing and the compiler-inspired transparent ranking formula:
FinalScore = 0.40 * K + 0.25 * S + 0.20 * R + 0.15 * C
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional, Tuple
from smartlex.extractors import (
    extract_text_from_file,
    split_into_sentences,
    tokenize_text,
    count_token_frequencies,
    ExtractionError
)


class SmartLexEngine:
    def __init__(self, db_path: str = "smartlex_index.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def close(self):
        """Optional explicit close hook (connections are scoped to method calls)."""
        pass

    def _init_db(self):
        """Initialize persistent SQLite tables for compiler-inspired symbol tables and document indices."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    filepath TEXT,
                    file_type TEXT,
                    raw_text TEXT,
                    token_count INTEGER,
                    indexed_at TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doc_tokens (
                    doc_id INTEGER,
                    token TEXT,
                    frequency INTEGER,
                    PRIMARY KEY (doc_id, token),
                    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doc_sentences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER,
                    sentence_idx INTEGER,
                    sentence_text TEXT,
                    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            # Indices for rapid lexical lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_token ON doc_tokens(token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentences_doc ON doc_sentences(doc_id)")
            conn.commit()

    def index_document(self, filepath: str) -> Dict[str, Any]:
        """
        Extracts, normalizes, tokenizes and stores a document in the SQLite database.
        Returns metadata about the indexed document.
        Raises ExtractionError or Exception on failure.
        """
        filename = os.path.basename(filepath)
        raw_text, file_type = extract_text_from_file(filepath)
        
        # Tokenize (full tokens for proximity & filtered for lexical analysis)
        full_tokens = tokenize_text(raw_text, remove_stopwords=False)
        content_tokens = tokenize_text(raw_text, remove_stopwords=True)
        token_freq = count_token_frequencies(content_tokens)
        sentences = split_into_sentences(raw_text)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # If document already exists, remove previous version first
            cursor.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
            existing = cursor.fetchone()
            if existing:
                doc_id = existing["id"]
                cursor.execute("DELETE FROM doc_tokens WHERE doc_id = ?", (doc_id,))
                cursor.execute("DELETE FROM doc_sentences WHERE doc_id = ?", (doc_id,))
                cursor.execute("""
                    UPDATE documents 
                    SET filepath = ?, file_type = ?, raw_text = ?, token_count = ?, indexed_at = ?
                    WHERE id = ?
                """, (filepath, file_type, raw_text, len(full_tokens), datetime.datetime.now(), doc_id))
            else:
                cursor.execute("""
                    INSERT INTO documents (filename, filepath, file_type, raw_text, token_count, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (filename, filepath, file_type, raw_text, len(full_tokens), datetime.datetime.now()))
                doc_id = cursor.lastrowid

            # Insert token frequencies into symbol table
            token_rows = [(doc_id, token, count) for token, count in token_freq.items()]
            cursor.executemany("INSERT INTO doc_tokens (doc_id, token, frequency) VALUES (?, ?, ?)", token_rows)

            # Insert sentence records
            sentence_rows = [(doc_id, idx, sent) for idx, sent in enumerate(sentences)]
            cursor.executemany("INSERT INTO doc_sentences (doc_id, sentence_idx, sentence_text) VALUES (?, ?, ?)", sentence_rows)

            conn.commit()

        return {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "token_count": len(full_tokens),
            "unique_terms": len(token_freq),
            "sentence_count": len(sentences)
        }

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Retrieve list of all currently indexed documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, filepath, file_type, token_count, indexed_at
                FROM documents
                ORDER BY id ASC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_document(self, doc_id: int):
        """Remove a document and its associated tokens and sentences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doc_tokens WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM doc_sentences WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

    def clear_index(self):
        """Clear all stored documents and indices."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doc_tokens")
            cursor.execute("DELETE FROM doc_sentences")
            cursor.execute("DELETE FROM documents")
            conn.commit()

    def _get_average_doc_length(self) -> float:
        """Calculate average token count across all documents for normalized similarity calculation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT AVG(token_count) as avg_len FROM documents")
            row = cursor.fetchone()
            if row and row["avg_len"]:
                return float(row["avg_len"])
            return 100.0

    def search(self, query_string: str) -> List[Dict[str, Any]]:
        """
        Executes compiler-inspired semantic retrieval for a natural-language query.
        Ranks matching documents using:
        FinalScore = 0.40 * K + 0.25 * S + 0.20 * R + 0.15 * C
        """
        raw_query = query_string.strip()
        if not raw_query:
            return []

        # Lexical analysis of the query
        query_tokens_all = tokenize_text(raw_query, remove_stopwords=False)
        query_tokens = tokenize_text(raw_query, remove_stopwords=True)
        if not query_tokens:
            query_tokens = query_tokens_all

        # Unique query terms for coverage calculations
        unique_query_terms = list(dict.fromkeys(query_tokens))
        num_query_terms = len(unique_query_terms)

        if num_query_terms == 0:
            return []

        avg_doc_len = self._get_average_doc_length()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Retrieve documents that match at least one query token
            placeholders = ",".join("?" for _ in unique_query_terms)
            sql = f"""
                SELECT DISTINCT d.id, d.filename, d.filepath, d.file_type, d.raw_text, d.token_count
                FROM documents d
                JOIN doc_tokens dt ON d.id = dt.doc_id
                WHERE dt.token IN ({placeholders})
            """
            cursor.execute(sql, unique_query_terms)
            candidate_docs = cursor.fetchall()

            if not candidate_docs:
                return []

            results = []

            for doc in candidate_docs:
                doc_id = doc["id"]
                raw_text = doc["raw_text"]
                doc_len = doc["token_count"] or 1

                # 1. Fetch term frequencies for this document
                cursor.execute(f"""
                    SELECT token, frequency 
                    FROM doc_tokens 
                    WHERE doc_id = ? AND token IN ({placeholders})
                """, [doc_id] + unique_query_terms)
                token_freq_rows = cursor.fetchall()
                term_frequencies = {row["token"]: row["frequency"] for row in token_freq_rows}

                matched_terms = [t for t in unique_query_terms if t in term_frequencies]
                
                # --- K: Query-term Coverage ---
                # Fraction of unique query terms present in the document
                K = len(matched_terms) / float(num_query_terms)

                # --- S: Local Similarity Score (Normalized TF / BM25-lite) ---
                # Sublinear saturated term frequency normalized by document length
                s_sum = 0.0
                k1 = 1.2
                b = 0.75
                len_norm = (1.0 - b) + b * (doc_len / avg_doc_len) if avg_doc_len > 0 else 1.0

                for t in unique_query_terms:
                    tf = term_frequencies.get(t, 0)
                    if tf > 0:
                        term_score = tf / (tf + k1 * len_norm)
                        s_sum += term_score

                S = min(1.0, s_sum / float(num_query_terms))

                # --- R: Basic Relationship / Pattern Match ---
                # Checks syntactic proximity and co-occurrence of adjacent query tokens
                R = self._compute_relationship_score(raw_text, query_tokens)

                # --- C: Query-term Coverage in the Best-Matching Sentence ---
                # Also extracts the best sentence for snippet evidence
                cursor.execute("""
                    SELECT sentence_text 
                    FROM doc_sentences 
                    WHERE doc_id = ? 
                    ORDER BY sentence_idx ASC
                """, (doc_id,))
                sentence_rows = cursor.fetchall()
                sentences = [row["sentence_text"] for row in sentence_rows]

                C, best_sentence, best_sent_matched = self._find_best_sentence(sentences, unique_query_terms)

                # --- Final Score Calculation ---
                final_score = (0.40 * K) + (0.25 * S) + (0.20 * R) + (0.15 * C)

                # Detailed explanation for transparency and faculty evaluation
                explanation = (
                    f"Final Score: {final_score:.4f} ({final_score*100:.1f}%)\n"
                    f"Formula: 0.40*K + 0.25*S + 0.20*R + 0.15*C\n\n"
                    f"• K = {K:.3f} (Coverage: {len(matched_terms)}/{num_query_terms} query terms found)\n"
                    f"  Weighted: 0.40 * {K:.3f} = {0.40 * K:.4f}\n\n"
                    f"• S = {S:.3f} (Local TF-Similarity: normalized term density)\n"
                    f"  Weighted: 0.25 * {S:.3f} = {0.25 * S:.4f}\n\n"
                    f"• R = {R:.3f} (Relationship: token pair proximity / collocation)\n"
                    f"  Weighted: 0.20 * {R:.3f} = {0.20 * R:.4f}\n\n"
                    f"• C = {C:.3f} (Best Sentence Coverage: {len(best_sent_matched)}/{num_query_terms} terms in single sentence)\n"
                    f"  Weighted: 0.15 * {C:.3f} = {0.15 * C:.4f}"
                )

                results.append({
                    "doc_id": doc_id,
                    "filename": doc["filename"],
                    "filepath": doc["filepath"],
                    "file_type": doc["file_type"],
                    "final_score": round(final_score, 4),
                    "score_k": round(K, 4),
                    "score_s": round(S, 4),
                    "score_r": round(R, 4),
                    "score_c": round(C, 4),
                    "matched_keywords": matched_terms,
                    "snippet": best_sentence,
                    "explanation": explanation
                })

            # Sort results descending by final_score
            results.sort(key=lambda x: x["final_score"], reverse=True)
            return results

    def _compute_relationship_score(self, text: str, query_tokens: List[str]) -> float:
        """
        Compiler-inspired syntactic proximity scoring (R).
        Examines whether adjacent query tokens co-occur within a local window in the document.
        """
        doc_words = tokenize_text(text, remove_stopwords=False)
        if not doc_words:
            return 0.0

        if len(query_tokens) <= 1:
            # Single term: check if term appears prominently (multiple times or in close proximity)
            single = query_tokens[0]
            count = sum(1 for w in doc_words if w == single)
            return 1.0 if count >= 2 else (0.6 if count == 1 else 0.0)

        # Build position index for words in document
        pos_map: Dict[str, List[int]] = {}
        for idx, word in enumerate(doc_words):
            pos_map.setdefault(word, []).append(idx)

        total_pairs = len(query_tokens) - 1
        matched_pairs = 0

        # Check each adjacent query pair (w1, w2)
        for i in range(total_pairs):
            w1 = query_tokens[i]
            w2 = query_tokens[i + 1]

            positions1 = pos_map.get(w1, [])
            positions2 = pos_map.get(w2, [])

            pair_found = False
            # Check if any occurrence is within 15 words of each other (local sentence/clause scope)
            for p1 in positions1:
                for p2 in positions2:
                    if 0 < abs(p1 - p2) <= 15:
                        pair_found = True
                        break
                if pair_found:
                    break

            if pair_found:
                matched_pairs += 1

        return float(matched_pairs) / float(total_pairs)

    def _find_best_sentence(self, sentences: List[str], unique_query_terms: List[str]) -> Tuple[float, str, List[str]]:
        """
        Finds the single sentence that maximizes query-term coverage (C)
        and returns (C_score, best_sentence_text, matched_terms_in_best_sentence).
        """
        if not sentences or not unique_query_terms:
            return 0.0, "", []

        best_score = 0.0
        best_sentence = sentences[0]
        best_matched: List[str] = []

        total_q = float(len(unique_query_terms))

        for sent in sentences:
            sent_tokens = set(tokenize_text(sent, remove_stopwords=False))
            matched = [t for t in unique_query_terms if t in sent_tokens]
            coverage = len(matched) / total_q

            if coverage > best_score:
                best_score = coverage
                best_sentence = sent
                best_matched = matched
            elif coverage == best_score and best_score > 0:
                # Tie-breaker: choose slightly more informative sentence (longer snippet up to 200 chars)
                if len(sent) > len(best_sentence):
                    best_sentence = sent

        # If no sentence had any matches, use the first sentence as fallback snippet
        if best_score == 0.0 and sentences:
            best_sentence = sentences[0]

        return best_score, best_sentence, best_matched
