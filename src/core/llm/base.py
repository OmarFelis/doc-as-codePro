"""Base interface for LLM clients."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMClient(ABC):
    """Abstract base class for Language Model clients."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            system_prompt: Optional system prompt for context

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def generate_documentation(
        self, code: str, context: Dict[str, Any]
    ) -> str:
        """
        Generate documentation for code.

        Args:
            code: Source code to document
            context: Additional context (language, file_path, etc.)

        Returns:
            Generated documentation
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM client is available and configured.

        Returns:
            True if available, False otherwise
        """
        pass
