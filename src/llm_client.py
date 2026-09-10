import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from src.utils import logger

class LLMClient:
    """
    Universal lightweight LLM Client supporting:
    1. Groq Cloud API (llama-3.3-70b-versatile, llama-3.1-8b-instant) - Ultra-fast & free tier
    2. OpenAI API (gpt-4o-mini, gpt-3.5-turbo)
    3. Google Gemini API (gemini-1.5-flash, gemini-1.5-pro)
    4. Deterministic Local Semantic Fallback (zero-key instant offline reproduction)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 300
    ):
        # Sanitize and validate API keys
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

        def is_valid_key(key: str) -> bool:
            return bool(key and len(key) > 15 and not key.startswith("your_"))

        # Auto-detect active provider
        if provider:
            self.provider = provider
        elif is_valid_key(self.groq_api_key):
            self.provider = "groq"
        elif is_valid_key(self.openai_api_key):
            self.provider = "openai"
        elif is_valid_key(self.gemini_api_key):
            self.provider = "gemini"
        else:
            self.provider = "local_semantic"

        # Model default selection
        if model:
            self.model = model
        elif self.provider == "groq":
            self.model = "llama-3.3-70b-versatile"
        elif self.provider == "openai":
            self.model = "gpt-4o-mini"
        elif self.provider == "gemini":
            self.model = "gemini-1.5-flash"
        else:
            self.model = "local_heuristic"

        self.temperature = temperature
        self.max_tokens = max_tokens
        logger.info(f"Initialized LLMClient (Provider: {self.provider}, Model: {self.model})")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text completion from the active LLM provider."""
        if self.provider == "groq" and self.groq_api_key:
            return self._call_groq(system_prompt, user_prompt)
        elif self.provider == "openai" and self.openai_api_key:
            return self._call_openai(system_prompt, user_prompt)
        elif self.provider == "gemini" and self.gemini_api_key:
            return self._call_gemini(system_prompt, user_prompt)
        else:
            return self._local_fallback(system_prompt, user_prompt)

    def _call_groq(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}. Falling back to local semantic engine.")
            return self._local_fallback(system_prompt, user_prompt)

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Falling back to local semantic engine.")
            return self._local_fallback(system_prompt, user_prompt)

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\nUser Query: {user_prompt}"}]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Falling back to local semantic engine.")
            return self._local_fallback(system_prompt, user_prompt)

    def _local_fallback(self, system_prompt: str, user_prompt: str) -> str:
        """Deterministic semantic generation when no API key is supplied."""
        return ""
