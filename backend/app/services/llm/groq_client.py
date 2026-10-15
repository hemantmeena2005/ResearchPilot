import logging
import os
import time
from typing import Any

from groq import APIConnectionError, APIError, Groq, RateLimitError

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqClientService:
    """Wrapper around official Groq Python SDK with retry, model validation, and provider abstraction."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        self.client: Groq | None = None
        if self.api_key and self.api_key.strip():
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")

    def is_configured(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
        response_format: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Call Groq API with exponential backoff on transient errors and graceful fallback."""
        if not self.is_configured():
            # Graceful local fallback response if no API key is provided
            return {
                "content": (
                    "**[Groq API Key Not Configured]**\n\n"
                    "To enable live LLM generation, set your `GROQ_API_KEY` in the `.env` file or environment. "
                    "You can obtain a free API key at [console.groq.com](https://console.groq.com/keys).\n\n"
                    "The local hybrid retrieval, vector search, and citation grounding pipeline is fully operational."
                ),
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": 1.0,
            }

        target_model = model or settings.GROQ_MODEL
        retries = settings.GROQ_MAX_RETRIES
        delay = 1.0
        start_time = time.time()

        for attempt in range(retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": settings.GROQ_TIMEOUT_SECONDS,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = self.client.chat.completions.create(**kwargs)
                latency_ms = (time.time() - start_time) * 1000

                usage = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }

                content = response.choices[0].message.content or ""
                return {
                    "content": content,
                    "token_usage": usage,
                    "latency_ms": latency_ms,
                }

            except RateLimitError as e:
                logger.warning(f"Groq Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise RuntimeError("Groq API quota exhausted or rate limit reached. Please try again shortly.")
                time.sleep(delay)
                delay *= 2

            except APIConnectionError as e:
                logger.warning(f"Groq connection error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise RuntimeError("Failed to connect to Groq API. Please check your network connection.")
                time.sleep(delay)
                delay *= 2

            except APIError as e:
                logger.error(f"Groq API error: {e}")
                raise RuntimeError(f"Groq provider error: {e!s}")
            except Exception as e:
                logger.error(f"Unexpected error calling Groq: {e}")
                raise RuntimeError(f"Generation failed: {e!s}")

        raise RuntimeError("Groq call exceeded maximum retry attempts.")
