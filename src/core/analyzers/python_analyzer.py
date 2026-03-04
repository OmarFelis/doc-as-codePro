"""Analizador de código Python usando AST."""
import ast
from pathlib import Path
from typing import List, Dict, Any

from src.core.analyzers.base import CodeAnalyzer
from src.models.domain import FileAnalysis, LanguageType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PythonAnalyzer(CodeAnalyzer):
    """Analizador de código Python usando AST."""
    
    @property
    def supported_languages(self) -> List[LanguageType]:
        return [LanguageType.PYTHON]
    
    def can_analyze(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.py', '.pyw']
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analiza archivo Python usando AST."""
        logger.info("analyzing_python_file", file_path=str(file_path))
        
        content = self._read_file_content(file_path)
        
        try:
            tree = ast.parse(content)
            visitor = PythonASTVisitor()
            visitor.visit(tree)
            
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.PYTHON,
                lines=self._count_lines(file_path),
                classes=visitor.classes,
                functions=visitor.functions,
                imports=visitor.imports,
                endpoints=visitor.endpoints,
                database_calls=visitor.database_calls,
                complexity=visitor.complexity,
                func_complexity=visitor.func_complexity,
            )
        except SyntaxError as e:
            logger.warning("syntax_error_in_file", file_path=str(file_path), error=str(e))
            return FileAnalysis(
                file_path=str(file_path),
                language=LanguageType.PYTHON,
                lines=self._count_lines(file_path)
            )


class PythonASTVisitor(ast.NodeVisitor):
    """Visitor para extraer información del AST de Python."""
    
    def __init__(self) -> None:
        self.classes: List[str] = []
        self.functions: List[str] = []
        self.imports: List[str] = []
        self.endpoints: List[Dict[str, Any]] = []
        self.database_calls: List[str] = []
        self.complexity = 0
        self._current_class: str | None = None
        self._func_complexity: Dict[str, int] = {}

    @property
    def func_complexity(self) -> Dict[str, int]:
        return self._func_complexity
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        prev = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visita definición de función (sync y async)."""
        func_name = f"{self._current_class}.{node.name}" if self._current_class else node.name
        self.functions.append(func_name)
        self._func_complexity[func_name] = self._calculate_complexity(node)

        _HTTP_METHODS = {'route', 'get', 'post', 'put', 'delete', 'patch'}
        for decorator in node.decorator_list:
            attr = None
            if isinstance(decorator, ast.Name) and decorator.id in _HTTP_METHODS:
                attr = decorator.id
            elif isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute) and func.attr in _HTTP_METHODS:
                    attr = func.attr
                elif isinstance(func, ast.Name) and func.id in _HTTP_METHODS:
                    attr = func.id
            if attr:
                self.endpoints.append({'function': func_name, 'decorator': attr, 'line': node.lineno})

        self.complexity += self._func_complexity[func_name]
        # Visitar el cuerpo sin propagar _current_class a funciones anidadas
        prev = self._current_class
        self._current_class = None
        self.generic_visit(node)
        self._current_class = prev

    visit_AsyncFunctionDef = visit_FunctionDef
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visita import."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visita import from."""
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visita llamadas a funciones (detectar DB calls)."""
        if isinstance(node.func, ast.Attribute):
            # Detectar patrones comunes de DB
            db_patterns = ['execute', 'query', 'find', 'save', 'delete', 'update', 'insert']
            if node.func.attr in db_patterns:
                self.database_calls.append(node.func.attr)
        self.generic_visit(node)
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcula complejidad ciclomática básica."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
