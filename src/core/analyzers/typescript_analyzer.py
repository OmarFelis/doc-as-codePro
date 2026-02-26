"""TypeScript code analyzer using tree-sitter."""

from pathlib import Path
from typing import List, Dict, Any
import re

from src.core.analyzers.base import CodeAnalyzer
from src.models.domain import FileAnalysis, LanguageType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TypeScriptAnalyzer(CodeAnalyzer):
    """
    Analyzer for TypeScript source files.
    
    Note: This is a simplified version using regex patterns.
    For production, consider using tree-sitter-typescript for full AST parsing.
    """

    @property
    def supported_languages(self) -> List[LanguageType]:
        """Return list of supported languages."""
        return [LanguageType.TYPESCRIPT]

    def can_analyze(self, file_path: Path) -> bool:
        """Check if this analyzer can handle the file."""
        return file_path.suffix.lower() in [".ts", ".tsx"]

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Analyze a TypeScript source file.

        Args:
            file_path: Path to the TypeScript file

        Returns:
            FileAnalysis with extracted information
        """
        content = self._read_file_content(file_path)

        try:
            # Extract information using regex patterns
            # For production, use tree-sitter for proper AST parsing
            classes = self._extract_classes(content)
            functions = self._extract_functions(content)
            interfaces = self._extract_interfaces(content)
            types = self._extract_types(content)
            imports = self._extract_imports(content)
            decorators = self._extract_decorators(content)
            endpoints = self._detect_framework_endpoints(content)

            # Combine classes and interfaces
            all_classes = classes + [f"{iface} (interface)" for iface in interfaces]
            all_classes.extend([f"{t} (type)" for t in types])

            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.TYPESCRIPT,
                lines=len(content.splitlines()),
                classes=all_classes,
                functions=functions,
                imports=imports,
                endpoints=endpoints,
                complexity=self._calculate_complexity(content),
            )

        except Exception as e:
            logger.error(
                "typescript_analysis_error", file_path=str(file_path), error=str(e)
            )
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.TYPESCRIPT,
                lines=len(content.splitlines()),
                classes=[],
                functions=[],
                imports=[],
                error=f"Analysis error: {str(e)}",
            )

    def _extract_classes(self, content: str) -> List[str]:
        """Extract class names."""
        pattern = r"class\s+([A-Za-z_][A-Za-z0-9_]*)"
        matches = re.findall(pattern, content)
        return matches

    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names."""
        patterns = [
            r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",  # function name()
            r"const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\(",  # const name = ()
            r"([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*:\s*[^{]+\{",  # name(): Type {
        ]

        functions = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            functions.extend(matches)

        return list(set(functions))  # Remove duplicates

    def _extract_interfaces(self, content: str) -> List[str]:
        """Extract interface names."""
        pattern = r"interface\s+([A-Za-z_][A-Za-z0-9_]*)"
        matches = re.findall(pattern, content)
        return matches

    def _extract_types(self, content: str) -> List[str]:
        """Extract type alias names."""
        pattern = r"type\s+([A-Za-z_][A-Za-z0-9_]*)\s*="
        matches = re.findall(pattern, content)
        return matches

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements."""
        patterns = [
            r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",  # import X from 'module'
            r"import\s+['\"]([^'\"]+)['\"]",  # import 'module'
        ]

        imports = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)

        return list(set(imports))

    def _extract_decorators(self, content: str) -> List[str]:
        """Extract decorator names."""
        pattern = r"@([A-Za-z_][A-Za-z0-9_]*)"
        matches = re.findall(pattern, content)
        return list(set(matches))

    def _detect_framework_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """
        Detect framework endpoints (Angular, NestJS, etc.).

        Looks for:
        - Angular: @Component, @Injectable
        - NestJS: @Controller, @Get, @Post, etc.
        """
        endpoints = []

        # NestJS controller endpoints
        if "@Controller" in content:
            # Extract controller path
            controller_match = re.search(r"@Controller\(['\"]([^'\"]*)['\"]?\)", content)
            base_path = controller_match.group(1) if controller_match else ""

            # Find HTTP method decorators
            method_patterns = [
                (r"@Get\(['\"]([^'\"]*)['\"]?\)", "GET"),
                (r"@Post\(['\"]([^'\"]*)['\"]?\)", "POST"),
                (r"@Put\(['\"]([^'\"]*)['\"]?\)", "PUT"),
                (r"@Delete\(['\"]([^'\"]*)['\"]?\)", "DELETE"),
                (r"@Patch\(['\"]([^'\"]*)['\"]?\)", "PATCH"),
            ]

            for pattern, method in method_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    route_path = match.group(1) if match.group(1) else ""
                    full_path = f"/{base_path}/{route_path}".replace("//", "/")
                    endpoints.append(
                        {
                            "http_method": method,
                            "path": full_path,
                            "framework": "nestjs",
                        }
                    )

        # Angular components/services (informational, not REST endpoints)
        if "@Component" in content:
            component_match = re.search(
                r"@Component\({[^}]*selector:\s*['\"]([^'\"]+)['\"]", content
            )
            if component_match:
                endpoints.append(
                    {
                        "type": "component",
                        "selector": component_match.group(1),
                        "framework": "angular",
                    }
                )

        return endpoints

    def _calculate_complexity(self, content: str) -> int:
        """
        Calculate cyclomatic complexity.

        Simple heuristic based on keywords.
        """
        complexity = 1  # Base complexity
        keywords = [
            r"\bif\b",
            r"\belse\s+if\b",
            r"\bwhile\b",
            r"\bfor\b",
            r"\bcase\b",
            r"\bcatch\b",
            r"\?\s*.*\s*:",  # Ternary operator
            r"\&\&",  # Logical AND
            r"\|\|",  # Logical OR
        ]

        for keyword in keywords:
            matches = re.findall(keyword, content)
            complexity += len(matches)

        return complexity
