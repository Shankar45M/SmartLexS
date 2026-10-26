"""
SmartLex-S Synonym-Aware Retrieval Engine.
Provides local synonym extraction using NLTK WordNet augmented with a specialized
compiler design / CS domain lexicon. Operates 100% locally with zero external network calls.
Includes synonym attenuation to prevent query semantic drift.
"""

import logging
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)

# Default attenuation factor for synonym-derived matches vs exact term matches
DEFAULT_SYNONYM_ATTENUATION = 0.70

# Curated domain knowledge for compiler design and document retrieval
COMPILER_DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    "scanner": ["lexer", "tokenizer", "tokenization"],
    "lexer": ["scanner", "tokenizer", "tokenization"],
    "tokenization": ["scanner", "lexer", "tokenizing", "tokens"],
    "tokens": ["token", "tokenization", "lexemes"],
    "parser": ["parsing", "syntax", "analyzer"],
    "parsing": ["parser", "syntax", "grammar"],
    "syntax": ["parser", "grammar", "parsing"],
    "grammar": ["syntax", "production", "bnf"],
    "optimization": ["optimizer", "optimizing", "improvement"],
    "optimizing": ["optimization", "improving"],
    "dead": ["unreachable", "unused"],
    "unreachable": ["dead", "unused"],
    "elimination": ["removal", "deletion"],
    "instructions": ["code", "statements", "operations"],
    "symbol": ["identifier", "lexeme"],
    "intermediate": ["ir", "three address code"],
    "generator": ["synthesis", "backend"],
}


class SynonymEngine:
    """
    Manages synonym expansion combining NLTK WordNet and compiler domain terminology.
    Employs POS filtering and attenuation weighting.
    """
    _instance: Optional["SynonymEngine"] = None

    def __init__(self, attenuation: float = DEFAULT_SYNONYM_ATTENUATION):
        self.attenuation = attenuation
        self._wn = None
        self._available: Optional[bool] = None

    @classmethod
    def get_instance(cls, attenuation: float = DEFAULT_SYNONYM_ATTENUATION) -> "SynonymEngine":
        """Singleton accessor for efficient reuse across search queries."""
        if cls._instance is None:
            cls._instance = cls(attenuation=attenuation)
        return cls._instance

    def is_available(self) -> bool:
        """Checks if NLTK WordNet is accessible locally."""
        if self._available is not None:
            return self._available

        try:
            from nltk.corpus import wordnet as wn
            # Quick probe
            _ = wn.synsets("test")
            self._wn = wn
            self._available = True
            logger.info("SynonymEngine: NLTK WordNet loaded successfully.")
        except Exception as e:
            logger.warning(f"SynonymEngine: WordNet unavailable, using domain thesaurus only: {e}")
            self._wn = None
            self._available = False

        return self._available

    def get_synonyms(self, word: str, max_synonyms: int = 3) -> List[str]:
        """
        Retrieves synonyms for a given single word.
        Integrates compiler domain overrides with WordNet noun/verb/adjective lemmas.
        Returns unique lowercase synonym strings, excluding the input word.
        """
        cleaned = word.lower().strip()
        if not cleaned or len(cleaned) <= 2:
            return []

        synonyms: List[str] = []
        seen: Set[str] = {cleaned}

        # 1. Check compiler domain thesaurus first (highest precision)
        if cleaned in COMPILER_DOMAIN_SYNONYMS:
            for s in COMPILER_DOMAIN_SYNONYMS[cleaned]:
                s_lower = s.lower().strip()
                if s_lower not in seen:
                    seen.add(s_lower)
                    synonyms.append(s_lower)
                    if len(synonyms) >= max_synonyms:
                        return synonyms

        # 2. Query WordNet if available
        if self.is_available() and self._wn is not None:
            try:
                # Filter by primary parts of speech: nouns ('n'), verbs ('v'), adjectives ('a', 's')
                allowed_pos = {'n', 'v', 'a', 's'}
                synsets = self._wn.synsets(cleaned)
                for syn in synsets:
                    if syn.pos() not in allowed_pos:
                        continue
                    for lemma in syn.lemmas():
                        candidate = lemma.name().lower().replace("_", " ").strip()
                        # Allow single-word synonyms or common compact pairs
                        if candidate not in seen and candidate.replace(" ", "").isalpha():
                            seen.add(candidate)
                            synonyms.append(candidate)
                            if len(synonyms) >= max_synonyms:
                                break
                    if len(synonyms) >= max_synonyms:
                        break
            except Exception as e:
                logger.warning(f"Error querying WordNet for '{word}': {e}")

        return synonyms[:max_synonyms]

    def expand_query_tokens(
        self, tokens: List[str], max_per_token: int = 3
    ) -> Dict[str, List[str]]:
        """
        Expands a list of query tokens into their respective synonym lists.
        Returns a dictionary mapping {token: [synonyms]}.
        """
        expansions: Dict[str, List[str]] = {}
        for t in tokens:
            t_clean = t.lower().strip()
            syns = self.get_synonyms(t_clean, max_synonyms=max_per_token)
            if syns:
                expansions[t_clean] = syns
        return expansions
