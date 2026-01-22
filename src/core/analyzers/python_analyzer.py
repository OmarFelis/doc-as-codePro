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
                complexity=visitor.complexity
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
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visita definición de clase."""
        self.classes.append(node.name)
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visita definición de función."""
        func_name = f"{self._current_class}.{node.name}" if self._current_class else node.name
        self.functions.append(func_name)
        
        # Detectar endpoints (decoradores comunes)
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ['route', 'get', 'post', 'put', 'delete', 'patch']:
                    self.endpoints.append({
                        'function': func_name,
                        'decorator': decorator.id,
                        'line': node.lineno
                    })
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ['route', 'get', 'post', 'put', 'delete', 'patch']:
                    self.endpoints.append({
                        'function': func_name,
                        'decorator': decorator.func.attr,
                        'line': node.lineno
                    })
        
        # Calcular complejidad ciclomática básica
        self.complexity += self._calculate_complexity(node)
        self.generic_visit(node)
    
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
