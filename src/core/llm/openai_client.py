"""OpenAI client for GPT models."""

import os
from typing import Dict, Any, Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.core.llm.base import LLMClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient(LLMClient):
    """Client for OpenAI GPT models."""

    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.warning("openai_not_available", message="openai library is not installed")
            self._client = None
            return

        settings = get_settings()
        
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("openai_no_api_key", message="OPENAI_API_KEY not set")
                self._client = None
                return

            self._client = AsyncOpenAI(api_key=api_key)
            self._model = os.environ.get("OPENAI_MODEL", "gpt-4")
            logger.info("openai_client_initialized", model=self._model)
        except Exception as e:
            logger.error("openai_init_error", error=str(e))
            self._client = None

    def is_available(self) -> bool:
        """Check if OpenAI client is available."""
        return self._client is not None

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text using GPT."""
        if not self.is_available():
            raise RuntimeError("OpenAI client is not available")

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error("openai_generation_error", error=str(e))
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    async def generate_documentation(
        self, code: str, context: Dict[str, Any]
    ) -> str:
        """Generate documentation for code using GPT."""
        language = context.get("language", "unknown")
        file_path = context.get("file_path", "")

        system_prompt = """You are an expert technical writer and software developer. 
Your task is to generate clear, comprehensive documentation for code."""

        prompt = f"""Generate professional documentation for the following {language} code:

File: {file_path}

```{language}
{code}
```

Please provide:
1. A brief description of what this code does
2. Key functions/classes and their purposes
3. Important implementation details
4. Any notable patterns or techniques used

Format the documentation in Markdown."""

        return await self.generate_text(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.5,
            system_prompt=system_prompt,
        )
