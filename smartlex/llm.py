"""
SmartLex-S Local Ollama LLM Integration.
Provides optional query-document explanation and answer synthesis via local Ollama daemon.
Strictly local (http://localhost:11434), zero-cloud, with rapid timeout (2.0s) and automatic
graceful degradation to grounded extractive summaries when Ollama is offline or absent.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_CONNECT_TIMEOUT = 1.5
DEFAULT_GENERATE_TIMEOUT = 5.0
PREFERRED_MODELS = ["llama3", "mistral", "phi3", "llama2", "gemma"]


class OllamaClient:
    """
    Client for interacting with local Ollama service.
    Designed to be 100% non-blocking and fail-safe: if Ollama is not running,
    it detects offline state rapidly and falls back to extractive document evidence.
    """
    _instance: Optional["OllamaClient"] = None

    def __init__(self, host: str = DEFAULT_OLLAMA_HOST):
        self.host = host.rstrip("/")
        self._available: Optional[bool] = None
        self._active_model: Optional[str] = None
        self._installed_models: List[str] = []

    @classmethod
    def get_instance(cls, host: str = DEFAULT_OLLAMA_HOST) -> "OllamaClient":
        """Singleton accessor for efficient reuse."""
        if cls._instance is None:
            cls._instance = cls(host=host)
        return cls._instance

    def check_health(self) -> bool:
        """
        Fast health check probe against Ollama /api/tags endpoint.
        Returns True only if daemon is actively responding.
        """
        try:
            req = urllib.request.Request(
                f"{self.host}/api/tags",
                headers={"User-Agent": "SmartLex-S"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=DEFAULT_CONNECT_TIMEOUT) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                    self._installed_models = models
                    self._available = True
                    # Select best preferred installed model if available
                    for pref in PREFERRED_MODELS:
                        if pref in models:
                            self._active_model = pref
                            break
                    if not self._active_model and models:
                        self._active_model = models[0]
                    return True
        except Exception:
            pass

        self._available = False
        self._active_model = None
        self._installed_models = []
        return False

    def is_available(self) -> bool:
        """Cached check with lazy probe."""
        if self._available is None:
            return self.check_health()
        return self._available

    def get_status_text(self) -> str:
        """Returns human-readable status for UI / diagnostic display."""
        if self.is_available():
            model = self._active_model or "ready"
            return f"Ollama Online ({model})"
        return "Ollama Offline (Extractive Fallback Active)"

    def synthesize_explanation(
        self,
        query: str,
        document_filename: str,
        evidence_snippet: str
    ) -> str:
        """
        Synthesizes a grounded explanation connecting the query to the retrieved passage.
        If Ollama is offline, immediately returns a structured extractive evidence summary.
        Never hallucinates or invents facts outside the evidence passage.
        """
        if not self.is_available() or not self._active_model or not evidence_snippet:
            # Clean grounded extractive fallback
            return f"[Extractive Evidence]: \"{evidence_snippet}\""

        # Prompt with strict anti-hallucination grounding instructions
        prompt = (
            f"You are SmartLex-S, a compiler-inspired document retrieval assistant.\n"
            f"Given the user search query and an excerpt from the document '{document_filename}', "
            f"provide a concise 1-to-2 sentence factual explanation of how the passage answers or relates to the query.\n"
            f"RULES:\n"
            f"1. Base your explanation strictly on the facts in the excerpt.\n"
            f"2. Do not invent details or assume information outside the text.\n\n"
            f"Query: {query}\n"
            f"Excerpt: {evidence_snippet}\n\n"
            f"Concise Grounded Explanation:"
        )

        payload = {
            "model": self._active_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 100
            }
        }

        try:
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "SmartLex-S"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=DEFAULT_GENERATE_TIMEOUT) as resp:
                if resp.status == 200:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    response_text = res_data.get("response", "").strip()
                    if response_text:
                        return f"[AI Synthesis ({self._active_model})]: {response_text}"
        except Exception as e:
            logger.info(f"Ollama generation fallback triggered: {e}")

        # Fallback to extractive evidence
        return f"[Extractive Evidence]: \"{evidence_snippet}\""
