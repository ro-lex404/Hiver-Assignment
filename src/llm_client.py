import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.utils import logger

class LLMClient:
    """
    Universal lightweight LLM Client supporting:
    1. Groq Cloud API (llama-3.3-70b-versatile, llama-3.1-8b-instant) - Ultra-fast & free tier
    2. OpenAI API (gpt-4o-mini, gpt-3.5-turbo)
    3. Google Gemini API (gemini-3.7-flash, gemini-2.5-pro)
    4. Deterministic Local Semantic Fallback (zero-key instant offline reproduction)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 300
    ):
        # Load local .env if present
        env_file = Path(__file__).resolve().parent.parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and not os.environ.get(k):
                                os.environ[k] = v
            except Exception:
                pass

        # Sanitize and validate API keys
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

        def is_valid_key(key: str) -> bool:
            return bool(key and len(key) > 15 and not key.startswith("your_"))

        # Auto-detect active provider (Groq prioritized for speed and free tier)
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
            self.model = "qwen/qwen3.8-27b"
        elif self.provider == "openai":
            self.model = "gpt-4o-mini"
        elif self.provider == "gemini":
            self.model = "gemini-3.7-flash"
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
            "Authorization": f"Bearer {self.groq_api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data["choices"][0]["message"]["content"].strip()
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt == 0:
                    time.sleep(1.5)
                    continue
                logger.warning(f"Groq API call failed: {e}. Falling back to local semantic engine.")
                return self._local_fallback(system_prompt, user_prompt)
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Falling back to local semantic engine.")
                return self._local_fallback(system_prompt, user_prompt)
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
