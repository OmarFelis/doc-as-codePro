"""JavaScript code analyzer using esprima."""

from pathlib import Path
from typing import List, Dict, Any
import esprima

from src.core.analyzers.base import CodeAnalyzer
from src.models.domain import FileAnalysis, LanguageType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JavaScriptAnalyzer(CodeAnalyzer):
    """Analyzer for JavaScript source files."""

    @property
    def supported_languages(self) -> List[LanguageType]:
        """Return list of supported languages."""
        return [LanguageType.JAVASCRIPT]

    def can_analyze(self, file_path: Path) -> bool:
        """Check if this analyzer can handle the file."""
        return file_path.suffix.lower() in [".js", ".mjs", ".cjs"]

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Analyze a JavaScript source file.

        Args:
            file_path: Path to the JavaScript file

        Returns:
            FileAnalysis with extracted information
        """
        content = self._read_file_content(file_path)

        try:
            # Parse JavaScript code
            tree = esprima.parseModule(content, {"loc": True, "tolerant": True})

            # Extract information
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            imports = self._extract_imports(tree)
            exports = self._extract_exports(tree)
            endpoints = self._detect_express_routes(content, tree)

            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.JAVASCRIPT,
                lines=len(content.splitlines()),
                classes=classes,
                functions=functions,
                imports=imports,
                endpoints=endpoints,
                complexity=self._calculate_complexity(tree),
            )

        except esprima.Error as e:
            logger.warning(
                "javascript_parse_error", file_path=str(file_path), error=str(e)
            )
            # Return partial analysis
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.JAVASCRIPT,
                lines=len(content.splitlines()),
                classes=[],
                functions=[],
                imports=[],
                error=f"Parse error: {str(e)}",
            )

        except Exception as e:
            logger.error(
                "javascript_analysis_error", file_path=str(file_path), error=str(e)
            )
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.JAVASCRIPT,
                lines=len(content.splitlines()),
                classes=[],
                functions=[],
                imports=[],
                error=f"Analysis error: {str(e)}",
            )

    def _extract_functions(self, tree: Any) -> List[str]:
        """Extract function names from the AST."""
        functions = []
        
        def traverse(node):
            if isinstance(node, dict):
                node_type = node.get("type")
                
                if node_type == "FunctionDeclaration":
                    if "id" in node and node["id"] and isinstance(node["id"], dict):
                        name = node["id"].get("name", "")
                        if name:
                            functions.append(name)
                
                elif node_type in ["FunctionExpression", "ArrowFunctionExpression"]:
                    # Check if this is assigned to a variable
                    if "id" in node and node["id"]:
                        name = node["id"].get("name", "")
                        if name:
                            functions.append(name)
                
                # Recurse through all properties
                for value in node.values():
                    traverse(value)
                    
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(tree)
        return functions

    def _extract_classes(self, tree: Any) -> List[str]:
        """Extract class names from the AST."""
        classes = []
        
        def traverse(node):
            if isinstance(node, dict):
                if node.get("type") == "ClassDeclaration":
                    if "id" in node and node["id"] and isinstance(node["id"], dict):
                        name = node["id"].get("name", "")
                        if name:
                            classes.append(name)
                
                # Recurse through all properties
                for value in node.values():
                    traverse(value)
                    
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(tree)
        return classes

    def _extract_imports(self, tree: Any) -> List[str]:
        """Extract import statements."""
        imports = []
        
        def traverse(node):
            if isinstance(node, dict):
                if node.get("type") == "ImportDeclaration":
                    source = node.get("source", {})
                    if isinstance(source, dict):
                        value = source.get("value", "")
                        if value:
                            imports.append(value)
                
                # Recurse
                for val in node.values():
                    traverse(val)
                    
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(tree)
        return imports

    def _extract_exports(self, tree: Dict[str, Any]) -> List[str]:
        """Extract export statements."""
        exports = []
        if "body" in tree:
            for node in tree["body"]:
                if node.get("type") in ["ExportNamedDeclaration", "ExportDefaultDeclaration"]:
                    # Extract export names
                    declaration = node.get("declaration", {})
                    if declaration:
                        if declaration.get("type") == "FunctionDeclaration":
                            name = declaration.get("id", {}).get("name", "")
                            if name:
                                exports.append(name)
                        elif declaration.get("type") == "ClassDeclaration":
                            name = declaration.get("id", {}).get("name", "")
                            if name:
                                exports.append(name)
        return exports

    def _detect_express_routes(
        self, content: str, tree: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect Express.js routes.

        Looks for patterns like:
        - app.get('/path', ...)
        - router.post('/path', ...)
        - express().use('/path', ...)
        """
        endpoints = []

        # Simple pattern matching for Express routes
        import re

        # Pattern: app.METHOD('/path', ...)
        patterns = [
            r"(app|router)\.(get|post|put|delete|patch|use)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"express\(\)\.(get|post|put|delete|patch|use)\s*\(\s*['\"]([^'\"]+)['\"]",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) == 3:
                    _, method, path = match.groups()
                    endpoints.append(
                        {
                            "http_method": method.upper(),
                            "path": path,
                            "framework": "express",
                        }
                    )
                elif len(match.groups()) == 2:
                    method, path = match.groups()
                    endpoints.append(
                        {
                            "http_method": method.upper(),
                            "path": path,
                            "framework": "express",
                        }
                    )

        return endpoints

    def _calculate_complexity(self, tree: Any) -> int:
        """
        Calculate cyclomatic complexity.

        Counts decision points in the code.
        """
        complexity = 1  # Base complexity
        decision_nodes = [
            "IfStatement",
            "WhileStatement",
            "ForStatement",
            "DoWhileStatement",
            "SwitchCase",
            "CatchClause",
            "ConditionalExpression",
            "LogicalExpression",
        ]

        def count_decisions(node: Any) -> None:
            nonlocal complexity
            if isinstance(node, dict):
                if node.get("type") in decision_nodes:
                    complexity += 1
                for value in node.values():
                    count_decisions(value)
            elif isinstance(node, list):
                for item in node:
                    count_decisions(item)

        count_decisions(tree)
        return complexity
