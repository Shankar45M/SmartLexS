"""
SmartLex-S Local Semantic Embedding Engine.
Provides local sentence/passage embeddings using Sentence Transformers (all-MiniLM-L6-v2),
vector serialization for SQLite BLOB storage, and fast cosine similarity computation.
Operates 100% locally with zero external API calls or telemetry.
"""

import logging
from typing import List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

# Default lightweight model (384 dimensions, ~80MB, optimized for CPU inference)
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class EmbeddingEngine:
    """
    Manages local embedding model loading, inference, vector serialization,
    and similarity scoring. Designed with lazy loading and robust fallback.
    """
    _instance: Optional["EmbeddingEngine"] = None

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._available: Optional[bool] = None

    @classmethod
    def get_instance(cls, model_name: str = DEFAULT_MODEL_NAME) -> "EmbeddingEngine":
        """Singleton accessor for efficient reuse across search requests."""
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def is_available(self) -> bool:
        """
        Checks whether the embedding model and dependencies are available locally.
        Attempts lazy load if not yet initialized.
        """
        if self._available is not None:
            return self._available
        
        try:
            from sentence_transformers import SentenceTransformer
            # Try loading or initializing the model
            self._model = SentenceTransformer(self.model_name)
            self._available = True
            logger.info(f"Loaded embedding model '{self.model_name}' successfully.")
        except Exception as e:
            logger.warning(f"Embedding model '{self.model_name}' unavailable: {e}")
            self._model = None
            self._available = False

        return self._available

    def _ensure_model(self) -> bool:
        """Ensures model is loaded in memory."""
        return self.is_available() and self._model is not None

    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Encodes a single text string into a normalized 1D float32 numpy vector (384-dim).
        Returns None if embedding model is unavailable or text is empty.
        """
        cleaned = text.strip() if text else ""
        if not cleaned:
            return None

        if not self._ensure_model():
            return None

        try:
            # normalize_embeddings=True ensures cosine similarity is equivalent to dot product
            emb = self._model.encode(cleaned, convert_to_numpy=True, normalize_embeddings=True)
            return emb.astype(np.float32)
        except Exception as e:
            logger.warning(f"Error encoding text: {e}")
            return None

    def encode_passages(self, passages: List[str], batch_size: int = 32) -> Optional[np.ndarray]:
        """
        Encodes a list of text passages into a 2D numpy array (N, 384).
        Returns None if model is unavailable or list is empty.
        """
        valid_passages = [p.strip() for p in passages if p and p.strip()]
        if not valid_passages:
            return None

        if not self._ensure_model():
            return None

        try:
            embeddings = self._model.encode(
                valid_passages,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.warning(f"Error encoding passages: {e}")
            return None

    @staticmethod
    def vector_to_blob(vec: np.ndarray) -> bytes:
        """Serializes a 1D float32 numpy vector to raw bytes for SQLite BLOB storage."""
        if not isinstance(vec, np.ndarray):
            vec = np.array(vec, dtype=np.float32)
        elif vec.dtype != np.float32:
            vec = vec.astype(np.float32)
        return vec.tobytes()

    @staticmethod
    def blob_to_vector(blob: bytes, dim: int = EMBEDDING_DIM) -> np.ndarray:
        """Deserializes SQLite BLOB bytes into a 1D float32 numpy array."""
        arr = np.frombuffer(blob, dtype=np.float32)
        if len(arr) != dim:
            # Handle potential dimension mismatch gracefully
            logger.warning(f"Vector dimension mismatch: expected {dim}, got {len(arr)}")
        return arr

    @staticmethod
    def compute_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Computes cosine similarity between two vectors.
        Since vectors are L2-normalized during encoding, dot product == cosine similarity.
        Clamped to [0.0, 1.0].
        """
        if vec_a is None or vec_b is None:
            return 0.0

        try:
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            if norm_a == 0.0 or norm_b == 0.0:
                return 0.0
            sim = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
            # Clamp between 0.0 and 1.0 (semantic similarity for retrieval is non-negative)
            return max(0.0, min(1.0, sim))
        except Exception as e:
            logger.warning(f"Similarity computation error: {e}")
            return 0.0

    @staticmethod
    def compute_matrix_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
        """
        Computes cosine similarity between a 1D query vector (D,) and a 2D document/sentence matrix (N, D).
        Returns 1D array of similarity scores of shape (N,).
        """
        if query_vec is None or doc_matrix is None or len(doc_matrix) == 0:
            return np.array([], dtype=np.float32)

        try:
            # Query norm
            q_norm = np.linalg.norm(query_vec)
            if q_norm == 0.0:
                return np.zeros(len(doc_matrix), dtype=np.float32)

            # Matrix norms along rows
            m_norms = np.linalg.norm(doc_matrix, axis=1)
            m_norms[m_norms == 0.0] = 1e-9

            dots = np.dot(doc_matrix, query_vec)
            sims = dots / (m_norms * q_norm)
            return np.clip(sims, 0.0, 1.0)
        except Exception as e:
            logger.warning(f"Matrix similarity error: {e}")
            return np.zeros(len(doc_matrix), dtype=np.float32)
