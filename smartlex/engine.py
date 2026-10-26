"""
SmartLex-S Core Retrieval Engine.
Implements SQLite persistent indexing and the hybrid transparent ranking formula:
FinalScore = 0.25 * K + 0.15 * S + 0.15 * R + 0.15 * C + 0.30 * E
(Supports baseline 4-factor formula when hybrid_scoring=False).
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
from smartlex.embeddings import EmbeddingEngine
from smartlex.synonyms import SynonymEngine
from smartlex.llm import OllamaClient


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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doc_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER,
                    sentence_idx INTEGER,
                    passage_text TEXT,
                    vector BLOB,
                    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)
            # Indices for rapid lexical & semantic lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_token ON doc_tokens(token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentences_doc ON doc_sentences(doc_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_doc ON doc_embeddings(doc_id)")
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
                cursor.execute("DELETE FROM doc_embeddings WHERE doc_id = ?", (doc_id,))
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

            # Generate and store sentence vector embeddings if model available
            emb_engine = EmbeddingEngine.get_instance()
            if emb_engine.is_available() and sentences:
                vectors = emb_engine.encode_passages(sentences)
                if vectors is not None:
                    emb_rows = [
                        (doc_id, idx, sent, EmbeddingEngine.vector_to_blob(vectors[idx]))
                        for idx, sent in enumerate(sentences)
                    ]
                    cursor.executemany(
                        "INSERT INTO doc_embeddings (doc_id, sentence_idx, passage_text, vector) VALUES (?, ?, ?, ?)",
                        emb_rows
                    )

            conn.commit()

        return {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "token_count": len(full_tokens),
            "unique_terms": len(token_freq),
            "sentence_count": len(sentences)
        }

    def backfill_embeddings(self) -> int:
        """
        Backfills vector embeddings for any documents in the database that lack embeddings.
        Returns the number of documents updated.
        """
        emb_engine = EmbeddingEngine.get_instance()
        if not emb_engine.is_available():
            return 0

        count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, raw_text FROM documents 
                WHERE id NOT IN (SELECT DISTINCT doc_id FROM doc_embeddings)
            """)
            missing_docs = cursor.fetchall()
            for doc in missing_docs:
                doc_id = doc["id"]
                cursor.execute("SELECT sentence_idx, sentence_text FROM doc_sentences WHERE doc_id = ? ORDER BY sentence_idx ASC", (doc_id,))
                s_rows = cursor.fetchall()
                if not s_rows:
                    continue
                sentences = [r["sentence_text"] for r in s_rows]
                vectors = emb_engine.encode_passages(sentences)
                if vectors is not None:
                    emb_rows = [
                        (doc_id, s_rows[idx]["sentence_idx"], sentences[idx], EmbeddingEngine.vector_to_blob(vectors[idx]))
                        for idx in range(len(sentences))
                    ]
                    cursor.executemany(
                        "INSERT INTO doc_embeddings (doc_id, sentence_idx, passage_text, vector) VALUES (?, ?, ?, ?)",
                        emb_rows
                    )
                    count += 1
            conn.commit()
        return count

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
            cursor.execute("DELETE FROM doc_embeddings WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

    def clear_index(self):
        """Clear all stored documents and indices."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doc_tokens")
            cursor.execute("DELETE FROM doc_sentences")
            cursor.execute("DELETE FROM doc_embeddings")
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

    def get_llm_status(self) -> str:
        """Returns the current status string of local Ollama LLM integration."""
        return OllamaClient.get_instance().get_status_text()

    def synthesize_explanation(self, query: str, result: Dict[str, Any]) -> str:
        """
        Generates a grounded natural language explanation for a search result item.
        Uses local Ollama if available, otherwise cleanly falls back to extractive evidence.
        """
        client = OllamaClient.get_instance()
        filename = result.get("filename", "document")
        snippet = result.get("snippet", "")
        return client.synthesize_explanation(query, filename, snippet)

    def search(
        self,
        query_string: str,
        hybrid_scoring: bool = True,
        synthesize_ai: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Executes compiler-inspired semantic retrieval for a natural-language query.
        Calculates lexical factors (K, S, R, C) and semantic factor (E).
        If hybrid_scoring is True (Phase 6):
            FinalScore = 0.25 * K + 0.15 * S + 0.15 * R + 0.15 * C + 0.30 * E
        Otherwise (Phase 1-3 baseline):
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

        # Synonym expansion via SynonymEngine
        syn_engine = SynonymEngine.get_instance()
        synonym_map: Dict[str, List[str]] = {}
        all_search_tokens_set = set(unique_query_terms)
        if syn_engine.is_available():
            synonym_map = syn_engine.expand_query_tokens(unique_query_terms, max_per_token=3)
            for syn_list in synonym_map.values():
                for s in syn_list:
                    for st in tokenize_text(s, remove_stopwords=True):
                        all_search_tokens_set.add(st)
        all_search_tokens_list = list(all_search_tokens_set)

        # Semantic query vector computation
        emb_engine = EmbeddingEngine.get_instance()
        query_vec = emb_engine.encode_text(raw_query) if emb_engine.is_available() else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Lexical candidate selection (includes exact terms and synonym expansions)
            placeholders = ",".join("?" for _ in all_search_tokens_list)
            sql = f"""
                SELECT DISTINCT d.id, d.filename, d.filepath, d.file_type, d.raw_text, d.token_count
                FROM documents d
                JOIN doc_tokens dt ON d.id = dt.doc_id
                WHERE dt.token IN ({placeholders})
            """
            cursor.execute(sql, all_search_tokens_list)
            candidate_map: Dict[int, Dict[str, Any]] = {row["id"]: dict(row) for row in cursor.fetchall()}

            # 2. Semantic candidate selection
            # Enables retrieving documents for paraphrase queries that have zero exact keyword overlap
            cursor.execute("SELECT id, filename, filepath, file_type, raw_text, token_count FROM documents")
            all_docs = {row["id"]: dict(row) for row in cursor.fetchall()}

            # Pre-compute document-level semantic similarity (E) and best semantic sentence
            doc_semantic_info: Dict[int, Dict[str, Any]] = {}
            if query_vec is not None:
                cursor.execute("SELECT doc_id, sentence_idx, passage_text, vector FROM doc_embeddings ORDER BY doc_id, sentence_idx")
                all_embs = cursor.fetchall()

                grouped_embs: Dict[int, List[Tuple[str, Any]]] = {}
                for row in all_embs:
                    d_id = row["doc_id"]
                    sent_txt = row["passage_text"]
                    vec = EmbeddingEngine.blob_to_vector(row["vector"])
                    grouped_embs.setdefault(d_id, []).append((sent_txt, vec))

                for d_id, s_list in grouped_embs.items():
                    best_sim = 0.0
                    best_sent = ""
                    for s_text, s_vec in s_list:
                        sim = EmbeddingEngine.compute_similarity(query_vec, s_vec)
                        if sim > best_sim:
                            best_sim = sim
                            best_sent = s_text
                    doc_semantic_info[d_id] = {
                        "score_e": best_sim,
                        "best_semantic_sentence": best_sent
                    }

                    # Include in candidates if notable semantic relevance (>= 0.35) or compact library (<= 100 docs)
                    if best_sim >= 0.35 or len(all_docs) <= 100:
                        if d_id in all_docs and d_id not in candidate_map:
                            candidate_map[d_id] = all_docs[d_id]

            if not candidate_map:
                return []

            results = []

            for doc_id, doc in candidate_map.items():
                raw_text = doc["raw_text"]
                doc_len = doc["token_count"] or 1

                # 1. Fetch term frequencies for this document (covering exact terms and synonyms)
                cursor.execute(f"""
                    SELECT token, frequency 
                    FROM doc_tokens 
                    WHERE doc_id = ? AND token IN ({placeholders})
                """, [doc_id] + all_search_tokens_list)
                token_freq_rows = cursor.fetchall()
                term_frequencies = {row["token"]: row["frequency"] for row in token_freq_rows}

                matched_terms: List[str] = []
                term_weights: List[float] = []
                s_sum = 0.0
                k1 = 1.2
                b = 0.75
                len_norm = (1.0 - b) + b * (doc_len / avg_doc_len) if avg_doc_len > 0 else 1.0

                for t in unique_query_terms:
                    if t in term_frequencies:
                        # Exact keyword match (weight 1.0)
                        tf = term_frequencies[t]
                        term_weights.append(1.0)
                        matched_terms.append(t)
                        term_score = tf / (tf + k1 * len_norm)
                        s_sum += term_score
                    else:
                        # Check synonym matches with attenuation
                        syns = synonym_map.get(t, [])
                        syn_matches = [s for s in syns if s in term_frequencies]
                        if syn_matches:
                            atten = syn_engine.attenuation
                            max_syn_tf = max(term_frequencies[s] for s in syn_matches)
                            eff_tf = atten * max_syn_tf
                            term_weights.append(atten)
                            matched_terms.append(f"{t}~{syn_matches[0]}")
                            term_score = eff_tf / (eff_tf + k1 * len_norm)
                            s_sum += term_score

                # --- K: Query-term Coverage (with synonym attenuation) ---
                K = min(1.0, sum(term_weights) / float(num_query_terms)) if num_query_terms > 0 else 0.0

                # --- S: Local Similarity Score (Normalized TF / BM25-lite) ---
                S = min(1.0, s_sum / float(num_query_terms)) if num_query_terms > 0 else 0.0

                # --- R: Basic Relationship / Pattern Match ---
                R = self._compute_relationship_score(raw_text, query_tokens)

                # --- C: Query-term Coverage in the Best-Matching Sentence ---
                cursor.execute("""
                    SELECT sentence_text 
                    FROM doc_sentences 
                    WHERE doc_id = ? 
                    ORDER BY sentence_idx ASC
                """, (doc_id,))
                sentence_rows = cursor.fetchall()
                sentences = [row["sentence_text"] for row in sentence_rows]

                C, best_sentence, best_sent_matched = self._find_best_sentence(sentences, unique_query_terms, synonym_map)

                # --- E: Semantic Embedding Similarity Score ---
                sem_info = doc_semantic_info.get(doc_id, {"score_e": 0.0, "best_semantic_sentence": ""})
                E = sem_info["score_e"]
                best_sem_sent = sem_info["best_semantic_sentence"]

                # If lexical sentence match is zero, grounded evidence snippet falls back to best semantic sentence
                if C == 0.0 and best_sem_sent:
                    best_sentence = best_sem_sent

                # --- Final Score Calculation ---
                if hybrid_scoring:
                    # Phase 6 5-factor formula: 0.25*K + 0.15*S + 0.15*R + 0.15*C + 0.30*E
                    final_score = (0.25 * K) + (0.15 * S) + (0.15 * R) + (0.15 * C) + (0.30 * E)
                    formula_str = "0.25*K + 0.15*S + 0.15*R + 0.15*C + 0.30*E"
                else:
                    # Baseline 4-factor formula: 0.40*K + 0.25*S + 0.20*R + 0.15*C
                    final_score = (0.40 * K) + (0.25 * S) + (0.20 * R) + (0.15 * C)
                    formula_str = "0.40*K + 0.25*S + 0.20*R + 0.15*C"

                final_score = max(0.0, min(1.0, final_score))

                # Detailed explanation for transparency and faculty evaluation
                if hybrid_scoring:
                    explanation = (
                        f"Final Score: {final_score:.4f} ({final_score*100:.1f}%)\n"
                        f"Formula: {formula_str}\n\n"
                        f"• K = {K:.3f} (Coverage: {len(matched_terms)}/{num_query_terms} query terms found)\n"
                        f"  Weighted: 0.25 * {K:.3f} = {0.25 * K:.4f}\n\n"
                        f"• S = {S:.3f} (Local TF-Similarity: normalized term density)\n"
                        f"  Weighted: 0.15 * {S:.3f} = {0.15 * S:.4f}\n\n"
                        f"• R = {R:.3f} (Relationship: token pair proximity / collocation)\n"
                        f"  Weighted: 0.15 * {R:.3f} = {0.15 * R:.4f}\n\n"
                        f"• C = {C:.3f} (Best Sentence Coverage: {len(best_sent_matched)}/{num_query_terms} terms in single sentence)\n"
                        f"  Weighted: 0.15 * {C:.3f} = {0.15 * C:.4f}\n\n"
                        f"• E = {E:.3f} (Semantic Embedding: local all-MiniLM-L6-v2 cosine similarity)\n"
                        f"  Weighted: 0.30 * {E:.3f} = {0.30 * E:.4f}"
                    )
                else:
                    explanation = (
                        f"Final Score: {final_score:.4f} ({final_score*100:.1f}%)\n"
                        f"Formula: {formula_str}\n\n"
                        f"• K = {K:.3f} (Coverage: {len(matched_terms)}/{num_query_terms} query terms found)\n"
                        f"  Weighted: 0.40 * {K:.3f} = {0.40 * K:.4f}\n\n"
                        f"• S = {S:.3f} (Local TF-Similarity: normalized term density)\n"
                        f"  Weighted: 0.25 * {S:.3f} = {0.25 * S:.4f}\n\n"
                        f"• R = {R:.3f} (Relationship: token pair proximity / collocation)\n"
                        f"  Weighted: 0.20 * {R:.3f} = {0.20 * R:.4f}\n\n"
                        f"• C = {C:.3f} (Best Sentence Coverage: {len(best_sent_matched)}/{num_query_terms} terms in single sentence)\n"
                        f"  Weighted: 0.15 * {C:.3f} = {0.15 * C:.4f}\n\n"
                        f"• E = {E:.3f} (Semantic Similarity: all-MiniLM-L6-v2 local vector cosine)"
                    )

                ai_explanation = None
                if synthesize_ai:
                    ai_explanation = OllamaClient.get_instance().synthesize_explanation(
                        raw_query, doc["filename"], best_sentence
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
                    "score_e": round(E, 4),
                    "matched_keywords": matched_terms,
                    "snippet": best_sentence,
                    "explanation": explanation,
                    "ai_explanation": ai_explanation
                })

            # Sort results descending by final_score, then score_e
            results.sort(key=lambda x: (x["final_score"], x.get("score_e", 0.0)), reverse=True)
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

    def _find_best_sentence(
        self,
        sentences: List[str],
        unique_query_terms: List[str],
        synonym_map: Optional[Dict[str, List[str]]] = None
    ) -> Tuple[float, str, List[str]]:
        """
        Finds the single sentence that maximizes query-term coverage (C)
        and returns (C_score, best_sentence_text, matched_terms_in_best_sentence).
        Accounts for exact matches (1.0) and attenuated synonym matches (0.70).
        """
        if not sentences or not unique_query_terms:
            return 0.0, "", []

        best_score = 0.0
        best_sentence = sentences[0]
        best_matched: List[str] = []

        total_q = float(len(unique_query_terms))
        syn_map = synonym_map or {}

        for sent in sentences:
            sent_tokens = set(tokenize_text(sent, remove_stopwords=False))
            matched_terms_in_sent: List[str] = []
            score_acc = 0.0

            for t in unique_query_terms:
                if t in sent_tokens:
                    score_acc += 1.0
                    matched_terms_in_sent.append(t)
                else:
                    syns = syn_map.get(t, [])
                    matching_syns = [s for s in syns if s in sent_tokens]
                    if matching_syns:
                        score_acc += 0.70
                        matched_terms_in_sent.append(f"{t}~{matching_syns[0]}")

            coverage = min(1.0, score_acc / total_q)

            if coverage > best_score:
                best_score = coverage
                best_sentence = sent
                best_matched = matched_terms_in_sent
            elif coverage == best_score and best_score > 0:
                # Tie-breaker: choose slightly more informative sentence (longer snippet up to 200 chars)
                if len(sent) > len(best_sentence):
                    best_sentence = sent

        # If no sentence had any matches, use the first sentence as fallback snippet
        if best_score == 0.0 and sentences:
            best_sentence = sentences[0]

        return best_score, best_sentence, best_matched

    def synthesize_explanation(self, query: str, res: Dict[str, Any]) -> str:
        """
        Synthesize a grounded explanation using local Ollama if available,
        or grounded extractive passage fallback.
        """
        ollama = OllamaClient.get_instance()
        return ollama.synthesize_explanation(
            query=query,
            document_filename=res.get("filename", ""),
            evidence_snippet=res.get("snippet", "")
        )
