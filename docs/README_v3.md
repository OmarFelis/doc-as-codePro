# 🚀 Doc-as-Code Service v3.0

Servicio moderno de documentación automática con IA, completamente refactorizado con arquitectura limpia y mejores prácticas.

## ✨ Características v3.0

- 🏗️ **Arquitectura Limpia**: Separación clara de responsabilidades
- 🔍 **Análisis AST Avanzado**: Soporte multi-lenguaje con analizadores especializados
- ⚡ **Procesamiento Paralelo**: Análisis concurrente de archivos
- 🧪 **Testing Completo**: >80% cobertura con pytest
- 📊 **Logging Estructurado**: Logs JSON con structlog
- ⚙️ **Configuración Centralizada**: Pydantic Settings con validación
- 🎯 **Type Safety**: Type hints completos con mypy
- 🔧 **Code Quality**: Black, Ruff, pre-commit hooks

## 📦 Instalación

### Requisitos
- Python 3.9+
- Poetry (recomendado) o pip

### Con Poetry (recomendado)
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Activar entorno virtual
poetry shell
```

### Con pip
```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

1. Copiar archivo de ejemplo:
```bash
cp .env.example .env
```

2. Editar `.env` con tus credenciales:
```env
OPENAI_API_KEY=sk-proj-your-key
CONFLUENCE_BASE_URL=https://your-instance.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your-token
# ... más configuraciones
```

## 🚀 Uso

### Análisis de Proyecto
```python
from pathlib import Path
from src.core.analyzers.project_analyzer import ProjectAnalyzerService

# Crear servicio
analyzer = ProjectAnalyzerService()

# Analizar proyecto
analysis = analyzer.analyze_project(
    project_path=Path("."),
    repository_name="my-project",
    repository_owner="my-org"
)

print(f"Archivos analizados: {analysis.total_files}")
print(f"Líneas de código: {analysis.total_lines}")
print(f"Lenguajes: {analysis.languages}")
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/unit/test_python_analyzer.py
```

## 🔧 Desarrollo

### Pre-commit Hooks
```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

### Linting y Formateo
```bash
# Formatear código
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

## 📁 Estructura del Proyecto

```
doc-as-code-service/
├── src/
│   ├── core/              # Lógica de negocio
│   │   ├── analyzers/     # Analizadores de código
│   │   ├── generators/    # Generadores de documentación
│   │   └── integrations/  # Integraciones externas
│   ├── api/               # FastAPI endpoints (próximamente)
│   ├── models/            # Modelos Pydantic
│   ├── config/            # Configuración
│   └── utils/             # Utilidades
├── tests/                 # Tests
│   ├── unit/             # Tests unitarios
│   └── integration/      # Tests de integración
├── infrastructure/        # IaC (próximamente)
└── ci-scripts/           # Scripts legacy (deprecados)
```

## 🎯 Roadmap

### ✅ Fase 1: Fundamentos (Completado)
- [x] Estructura de proyecto con arquitectura limpia
- [x] Configuración centralizada con Pydantic
- [x] Logging estructurado con structlog
- [x] Analizador Python con AST
- [x] Tests unitarios básicos
- [x] Pre-commit hooks

### 🚧 Fase 2: Modernización (En Progreso)
- [ ] API REST con FastAPI
- [ ] Más analizadores (Java, JavaScript, TypeScript)
- [ ] Generadores de documentación
- [ ] Integración con Confluence/Jira
- [ ] Cache con Redis

### 📋 Fase 3: Optimización (Planeado)
- [ ] Procesamiento asíncrono con Celery
- [ ] Base de datos PostgreSQL
- [ ] Métricas con Prometheus
- [ ] Diagramas inteligentes

### 🔮 Fase 4: Infraestructura (Futuro)
- [ ] Kubernetes deployment
- [ ] Terraform IaC
- [ ] CI/CD completo

## 📝 Migración desde v2.0

Los scripts legacy en `ci-scripts/` seguirán funcionando pero están deprecados. 
Para migrar a v3.0:

1. Usar nuevos analizadores en `src/core/analyzers/`
2. Configurar con `.env` en lugar de variables hardcoded
3. Usar logging estructurado en lugar de prints
4. Escribir tests para nuevas funcionalidades

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📄 Licencia

Propiedad de Alignet - Ecosistema de Pagos Digitales

---

**Versión:** 3.0.0  
**Estado:** En Desarrollo Activo  
**Mantenedor:** Alignet Tech Team
