# 🚀 Quick Start - Doc-as-Code Service v3.0

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Instalar Dependencias

```bash
# Opción A: Con Poetry (recomendado)
pip install poetry
poetry install

# Opción B: Con pip
pip install pydantic pydantic-settings structlog
```

### 2️⃣ Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env (mínimo requerido para testing local)
# Solo necesitas estas para probar:
DEBUG=true
OPENAI_API_KEY=sk-test-dummy  # Opcional para análisis básico
```

### 3️⃣ Ejecutar Ejemplo

```bash
# Con Poetry
poetry run python example.py

# O sin Poetry
python example.py
```

### 4️⃣ Ver Resultados

Deberías ver logs estructurados como:
```json
{
  "event": "starting_example",
  "message": "Iniciando análisis de ejemplo",
  "service": "doc-as-code-service",
  "timestamp": "2024-01-15T10:30:00.123456Z"
}
```

## 🧪 Ejecutar Tests

```bash
# Instalar pytest
pip install pytest pytest-cov

# Ejecutar tests
pytest

# Con coverage
pytest --cov=src --cov-report=term-missing
```

## 📝 Ejemplo de Código

```python
from pathlib import Path
from src.core.analyzers import ProjectAnalyzerService
from src.utils.logging import setup_logging, get_logger

# Setup
setup_logging(debug=True)
logger = get_logger(__name__)

# Analizar proyecto
analyzer = ProjectAnalyzerService()
analysis = analyzer.analyze_project(
    project_path=Path("."),
    repository_name="my-project"
)

# Ver resultados
logger.info(
    "analysis_complete",
    files=analysis.total_files,
    lines=analysis.total_lines,
    languages=[lang.value for lang in analysis.languages]
)
```

## 🔧 Troubleshooting

### Error: "No module named 'src'"
```bash
# Asegúrate de estar en el directorio raíz del proyecto
cd /path/to/doc-as-code-service
python example.py
```

### Error: "pydantic_settings not found"
```bash
pip install pydantic-settings
```

### Error: "structlog not found"
```bash
pip install structlog
```

## 📚 Siguiente Paso

Lee `FASE1_COMPLETADA.md` para entender la arquitectura completa.

## 💬 Preguntas Frecuentes

**P: ¿Necesito todas las variables de entorno?**  
R: No, para testing local solo necesitas `DEBUG=true`. Las demás son para producción.

**P: ¿Funciona con Python 3.8?**  
R: Requiere Python 3.9+ por el uso de type hints modernos.

**P: ¿Puedo usar el código legacy?**  
R: Sí, los scripts en `ci-scripts/` siguen funcionando, pero están deprecados.

**P: ¿Cómo agrego soporte para Java?**  
R: Crea `JavaAnalyzer` heredando de `CodeAnalyzer` y regístralo en `AnalyzerFactory`.

---

**¡Listo para comenzar!** 🎉
