"""
SmartLex-S: Compiler-Inspired Hybrid Intelligent Retrieval Engine.
"""
from smartlex.engine import SmartLexEngine
from smartlex.embeddings import EmbeddingEngine
from smartlex.synonyms import SynonymEngine
from smartlex.llm import OllamaClient

__version__ = "2.0.0"
__all__ = ["SmartLexEngine", "EmbeddingEngine", "SynonymEngine", "OllamaClient"]
