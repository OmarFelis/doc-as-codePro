"""Base interface for documentation generators."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from src.models.domain import ProjectAnalysis


class DocumentationGenerator(ABC):
    """Base class for documentation generators."""

    @abstractmethod
    async def generate(self, analysis: ProjectAnalysis) -> str:
        """
        Generate documentation from project analysis.

        Args:
            analysis: Project analysis result

        Returns:
            Generated documentation as string
        """
        pass
