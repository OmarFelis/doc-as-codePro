"""Java code analyzer using javalang."""

from pathlib import Path
from typing import List, Dict, Any
import javalang

from src.core.analyzers.base import CodeAnalyzer
from src.models.domain import FileAnalysis, LanguageType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JavaAnalyzer(CodeAnalyzer):
    """Analyzer for Java source files."""

    @property
    def supported_languages(self) -> List[LanguageType]:
        """Return list of supported languages."""
        return [LanguageType.JAVA]

    def can_analyze(self, file_path: Path) -> bool:
        """Check if this analyzer can handle the file."""
        return file_path.suffix.lower() == ".java"

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Analyze a Java source file.

        Args:
            file_path: Path to the Java file

        Returns:
            FileAnalysis with extracted information
        """
        content = self._read_file_content(file_path)

        try:
            # Parse Java code
            tree = javalang.parse.parse(content)

            # Extract information
            classes = self._extract_classes(tree)
            methods = self._extract_methods(tree)
            imports = self._extract_imports(tree)
            endpoints = self._detect_spring_endpoints(tree)
            database_entities = self._detect_jpa_entities(tree)

            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.JAVA,
                lines=len(content.splitlines()),
                classes=classes,
                functions=methods,
                imports=imports,
                endpoints=endpoints,
                database_calls=database_entities,
                complexity=self._calculate_complexity(tree),
            )

        except javalang.parser.JavaSyntaxError as e:
            logger.warning(
                "java_syntax_error", file_path=str(file_path), error=str(e)
            )
            # Return partial analysis even on syntax error
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.JAVA,
                lines=len(content.splitlines()),
                classes=[],
                functions=[],
                imports=[],
                error=f"Syntax error: {str(e)}",
            )

        except Exception as e:
            logger.error(
                "java_analysis_error", file_path=str(file_path), error=str(e)
            )
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.JAVA,
                lines=len(content.splitlines()),
                classes=[],
                functions=[],
                imports=[],
                error=f"Analysis error: {str(e)}",
            )

    def _extract_classes(self, tree: javalang.tree.CompilationUnit) -> List[str]:
        """Extract class names from the AST."""
        classes = []
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                classes.append(node.name)
            elif isinstance(node, javalang.tree.InterfaceDeclaration):
                classes.append(f"{node.name} (interface)")
            elif isinstance(node, javalang.tree.EnumDeclaration):
                classes.append(f"{node.name} (enum)")
        return classes

    def _extract_methods(self, tree: javalang.tree.CompilationUnit) -> List[str]:
        """Extract method names from the AST."""
        methods = []
        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                # Include class name for context
                class_name = self._get_parent_class_name(path)
                if class_name:
                    methods.append(f"{class_name}.{node.name}")
                else:
                    methods.append(node.name)
        return methods

    def _extract_imports(self, tree: javalang.tree.CompilationUnit) -> List[str]:
        """Extract import statements."""
        imports = []
        for path, node in tree:
            if isinstance(node, javalang.tree.Import):
                imports.append(node.path)
        return imports

    def _detect_spring_endpoints(
        self, tree: javalang.tree.CompilationUnit
    ) -> List[Dict[str, Any]]:
        """
        Detect Spring Boot REST endpoints.

        Looks for annotations like @GetMapping, @PostMapping, @RequestMapping, etc.
        """
        endpoints = []

        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                if node.annotations:
                    for annotation in node.annotations:
                        annotation_name = annotation.name
                        if annotation_name in [
                            "GetMapping",
                            "PostMapping",
                            "PutMapping",
                            "DeleteMapping",
                            "PatchMapping",
                            "RequestMapping",
                        ]:
                            # Extract path from annotation
                            endpoint_path = self._extract_mapping_path(annotation)
                            http_method = self._annotation_to_http_method(
                                annotation_name
                            )

                            endpoints.append(
                                {
                                    "method": node.name,
                                    "http_method": http_method,
                                    "path": endpoint_path,
                                    "annotation": annotation_name,
                                }
                            )

        return endpoints

    def _detect_jpa_entities(
        self, tree: javalang.tree.CompilationUnit
    ) -> List[str]:
        """
        Detect JPA/Hibernate entities.

        Looks for @Entity, @Table annotations.
        """
        entities = []

        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                if node.annotations:
                    for annotation in node.annotations:
                        if annotation.name in ["Entity", "Table", "MappedSuperclass"]:
                            entities.append(node.name)
                            break

        return entities

    def _extract_mapping_path(self, annotation: Any) -> str:
        """Extract path from Spring mapping annotation."""
        # Try to get value from annotation
        if hasattr(annotation, "element") and annotation.element:
            if isinstance(annotation.element, javalang.tree.Literal):
                # Simple string literal
                return annotation.element.value.strip('"')
            elif hasattr(annotation.element, "values"):
                # Array of values
                values = annotation.element.values
                if values and len(values) > 0:
                    first_value = values[0]
                    if isinstance(first_value, javalang.tree.Literal):
                        return first_value.value.strip('"')

        return "/"  # Default path

    def _annotation_to_http_method(self, annotation_name: str) -> str:
        """Convert annotation name to HTTP method."""
        mapping = {
            "GetMapping": "GET",
            "PostMapping": "POST",
            "PutMapping": "PUT",
            "DeleteMapping": "DELETE",
            "PatchMapping": "PATCH",
            "RequestMapping": "ANY",
        }
        return mapping.get(annotation_name, "UNKNOWN")

    def _get_parent_class_name(self, path: List) -> str:
        """Get the parent class name from AST path."""
        for node in reversed(path):
            if isinstance(node, javalang.tree.ClassDeclaration):
                return node.name
        return ""

    def _calculate_complexity(self, tree: javalang.tree.CompilationUnit) -> int:
        """
        Calculate cyclomatic complexity.

        Simple heuristic: count decision points.
        """
        complexity = 1  # Base complexity

        for path, node in tree:
            # Count control flow statements
            if isinstance(
                node,
                (
                    javalang.tree.IfStatement,
                    javalang.tree.WhileStatement,
                    javalang.tree.ForStatement,
                    javalang.tree.DoStatement,
                    javalang.tree.SwitchStatement,
                    javalang.tree.CatchClause,
                ),
            ):
                complexity += 1

        return complexity
