"""Tests para el analizador de Python."""
import pytest
from pathlib import Path
from src.core.analyzers.python_analyzer import PythonAnalyzer
from src.models.domain import LanguageType


@pytest.fixture
def python_analyzer():
    """Fixture del analizador de Python."""
    return PythonAnalyzer()


@pytest.fixture
def sample_python_file(tmp_path):
    """Crea un archivo Python de ejemplo."""
    file_path = tmp_path / "sample.py"
    content = '''
"""Sample Python module."""
import os
from typing import List

class SampleClass:
    """Sample class."""
    
    def method_one(self) -> str:
        """Sample method."""
        return "hello"
    
    def method_two(self, value: int) -> int:
        """Another method."""
        if value > 0:
            return value * 2
        return 0

def standalone_function(items: List[str]) -> int:
    """Standalone function."""
    count = 0
    for item in items:
        if item:
            count += 1
    return count
'''
    file_path.write_text(content)
    return file_path


def test_can_analyze_python_file(python_analyzer):
    """Test que puede analizar archivos Python."""
    assert python_analyzer.can_analyze(Path("test.py"))
    assert python_analyzer.can_analyze(Path("test.pyw"))
    assert not python_analyzer.can_analyze(Path("test.java"))


def test_analyze_python_file(python_analyzer, sample_python_file):
    """Test análisis de archivo Python."""
    analysis = python_analyzer.analyze_file(sample_python_file)
    
    assert analysis.language == LanguageType.PYTHON
    assert analysis.file_path == str(sample_python_file)
    assert len(analysis.classes) == 1
    assert "SampleClass" in analysis.classes
    assert len(analysis.functions) >= 3
    assert len(analysis.imports) >= 2
    assert analysis.lines > 0


def test_supported_languages(python_analyzer):
    """Test lenguajes soportados."""
    assert LanguageType.PYTHON in python_analyzer.supported_languages
