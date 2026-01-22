# 🤖 GUÍA PARA NUEVO AGENTE / NUEVO REPOSITORIO

## 📋 Contexto Rápido

Este es **doc-as-codePRO v3.0**, un servicio modernizado de documentación automática con IA.

### ¿Qué es este proyecto?
- Sistema de análisis de código con AST
- Generación automática de documentación técnica
- Arquitectura limpia con SOLID principles
- Type safety 100% con Pydantic
- Logging estructurado con structlog

### ¿De dónde viene?
- Modernización de un sistema legacy (v2.0)
- Fase 1 completada (Fundamentos)
- Listo para Fase 2 (API REST + más features)

## 🚀 Inicio Inmediato (3 pasos)

### 1. Leer Contexto (5 min)
```bash
cat docs/CONTEXTO_PROYECTO.md
```

### 2. Instalar y Probar (5 min)
```bash
poetry install
poetry run python example.py
```

### 3. Ejecutar Tests (2 min)
```bash
poetry run pytest
```

## 📚 Documentación Disponible

Toda la documentación está en la carpeta `docs/`:

### Esenciales (Leer primero)
1. **README.md** (este archivo) - Guía para nuevo agente
2. **CONTEXTO_PROYECTO.md** - Resumen del proyecto
3. **QUICKSTART.md** - Inicio rápido

### Técnicos
4. **README_v3.md** - Documentación completa
5. **ARQUITECTURA_VISUAL.md** - Diagramas y flujos
6. **FASE1_COMPLETADA.md** - Detalles de implementación

### Referencia
7. **RESUMEN_EJECUTIVO.md** - Para stakeholders
8. **CHECKLIST_FASE1.md** - Validación completa
9. **INDICE_DOCUMENTACION.md** - Índice maestro
10. **ORGANIZACION_PROYECTO.md** - Contexto histórico

## 🏗️ Estructura del Proyecto

```
doc-as-codePRO/
├── src/                    # Código fuente
│   ├── config/            # Pydantic Settings
│   ├── models/            # Domain models
│   ├── core/
│   │   └── analyzers/     # Analizadores de código
│   └── utils/             # Logging, utilidades
│
├── tests/                 # Tests con pytest
│   ├── unit/             # Tests unitarios
│   └── integration/      # Tests de integración
│
├── docs/                  # 📚 TODA LA DOCUMENTACIÓN
│
├── infrastructure/        # IaC (futuro)
│
├── pyproject.toml         # Poetry + configuración
├── .env.example           # Template de variables
├── .pre-commit-config.yaml # Hooks de calidad
└── example.py             # Script de ejemplo
```

## 🎯 Estado Actual del Proyecto

### ✅ Completado (Fase 1)
- Arquitectura limpia implementada
- Analizador Python con AST
- Sistema de configuración (Pydantic)
- Logging estructurado (structlog)
- Testing framework (pytest)
- Documentación completa

### 🚧 Siguiente (Fase 2)
- API REST con FastAPI
- Analizadores Java, JavaScript, TypeScript
- Generadores de documentación
- Integración Confluence/Jira
- Cache con Redis

### 📋 Futuro (Fase 3-4)
- Procesamiento asíncrono (Celery)
- Base de datos (PostgreSQL)
- Métricas (Prometheus)
- Kubernetes + Terraform

## 💻 Comandos Útiles

### Desarrollo
```bash
# Instalar dependencias
poetry install

# Activar entorno virtual
poetry shell

# Ejecutar ejemplo
python example.py

# Ejecutar tests
pytest

# Con coverage
pytest --cov=src --cov-report=html

# Formatear código
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

### Pre-commit
```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

## 🔍 Puntos de Entrada del Código

### 1. Configuración
```python
from src.config import get_settings

settings = get_settings()
print(settings.openai.api_key)
```

### 2. Análisis de Proyecto
```python
from pathlib import Path
from src.core.analyzers import ProjectAnalyzerService

analyzer = ProjectAnalyzerService()
analysis = analyzer.analyze_project(
    project_path=Path("."),
    repository_name="my-project"
)
```

### 3. Logging
```python
from src.utils.logging import setup_logging, get_logger

setup_logging(debug=True)
logger = get_logger(__name__)
logger.info("mensaje", key="value")
```

## 🎨 Patrones de Diseño Usados

### Strategy Pattern
```python
# Interfaz base
class CodeAnalyzer(ABC):
    @abstractmethod
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        pass

# Implementaciones
class PythonAnalyzer(CodeAnalyzer):
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        # Análisis con AST
        ...
```

### Factory Pattern
```python
class AnalyzerFactory:
    def get_analyzer(self, file_path: Path) -> CodeAnalyzer:
        # Retorna el analizador apropiado
        ...
```

### Singleton Pattern
```python
def get_settings() -> Settings:
    # Retorna instancia única de configuración
    ...
```

## 📊 Métricas de Calidad

- **Type safety**: 100% (mypy)
- **Cobertura tests**: ~60% (target 80%)
- **Complejidad**: Baja (<10)
- **Líneas de código**: ~890
- **Archivos**: 15
- **Mantenibilidad**: Alta

## 🐛 Troubleshooting Común

### Error: "No module named 'src'"
```bash
# Asegúrate de estar en el directorio raíz
cd /path/to/doc-as-codePRO
python example.py
```

### Error: "pydantic_settings not found"
```bash
pip install pydantic-settings
# O con poetry
poetry add pydantic-settings
```

### Error: Tests fallan
```bash
# Reinstalar dependencias
poetry install
# Ejecutar tests con verbose
pytest -v
```

## 🎓 Conceptos Clave

### Pydantic Settings
- Validación automática de configuración
- Carga desde .env
- Type-safe
- Auto-documentado

### structlog
- Logs JSON estructurados
- Contexto automático
- Modo dev (colorizado) vs prod (JSON)

### AST (Abstract Syntax Tree)
- Análisis estático de código Python
- Extrae estructura sin ejecutar
- Más preciso que regex

### Poetry
- Gestión moderna de dependencias
- Lock file reproducible
- Entornos virtuales automáticos

## 🔄 Flujo de Trabajo Típico

### Para Agregar un Nuevo Analizador
1. Crear clase en `src/core/analyzers/`
2. Heredar de `CodeAnalyzer`
3. Implementar métodos abstractos
4. Registrar en `AnalyzerFactory`
5. Agregar tests en `tests/unit/`

### Para Agregar una Nueva Feature
1. Crear modelos en `src/models/`
2. Implementar lógica en `src/core/`
3. Agregar configuración en `src/config/`
4. Escribir tests en `tests/`
5. Actualizar documentación

## 📞 Preguntas Frecuentes

**P: ¿Necesito leer toda la documentación?**  
R: No. Empieza con CONTEXTO_PROYECTO.md y QUICKSTART.md (10 min).

**P: ¿Dónde está el código legacy?**  
R: No está en este repo. Este es el proyecto modernizado (v3.0).

**P: ¿Puedo modificar el código?**  
R: Sí, pero sigue los patrones existentes y agrega tests.

**P: ¿Cómo contribuyo?**  
R: Lee README_v3.md sección "Contribuir" y usa pre-commit hooks.

**P: ¿Qué viene después?**  
R: Fase 2 - API REST con FastAPI. Ver FASE1_COMPLETADA.md.

## 🎯 Tareas Sugeridas para Nuevo Agente

### Familiarización (30 min)
1. [ ] Leer CONTEXTO_PROYECTO.md
2. [ ] Leer QUICKSTART.md
3. [ ] Ejecutar example.py
4. [ ] Revisar estructura en src/
5. [ ] Ejecutar tests

### Exploración (1 hora)
6. [ ] Leer ARQUITECTURA_VISUAL.md
7. [ ] Revisar código en src/core/analyzers/
8. [ ] Entender PythonAnalyzer
9. [ ] Revisar tests en tests/unit/
10. [ ] Leer FASE1_COMPLETADA.md

### Profundización (2 horas)
11. [ ] Leer README_v3.md completo
12. [ ] Entender patrones de diseño
13. [ ] Revisar configuración (Pydantic)
14. [ ] Entender logging (structlog)
15. [ ] Planear Fase 2

## ✅ Checklist de Validación

### Instalación
- [ ] Poetry instalado
- [ ] Dependencias instaladas (`poetry install`)
- [ ] Entorno virtual activado (`poetry shell`)

### Ejecución
- [ ] example.py ejecuta sin errores
- [ ] Tests pasan (`pytest`)
- [ ] Pre-commit hooks funcionan

### Comprensión
- [ ] Entiendo la arquitectura
- [ ] Entiendo los patrones usados
- [ ] Sé dónde está cada cosa
- [ ] Puedo agregar un nuevo analizador

## 🚀 Próximos Pasos Recomendados

1. **Leer documentación esencial** (15 min)
   - CONTEXTO_PROYECTO.md
   - QUICKSTART.md

2. **Instalar y probar** (10 min)
   - poetry install
   - python example.py
   - pytest

3. **Entender arquitectura** (30 min)
   - ARQUITECTURA_VISUAL.md
   - Revisar src/

4. **Planear siguiente fase** (30 min)
   - FASE1_COMPLETADA.md
   - Identificar tareas Fase 2

---

## 📖 Resumen de 30 Segundos

**¿Qué es?** Sistema de análisis de código con IA  
**¿Estado?** Fase 1 completada, listo para Fase 2  
**¿Cómo empezar?** `poetry install && python example.py`  
**¿Documentación?** Todo en carpeta `docs/`  
**¿Siguiente?** API REST con FastAPI (Fase 2)  

---

**Última actualización:** Enero 2025  
**Versión:** 3.0.0  
**Para:** Nuevo agente / Nuevo repositorio  
**Propósito:** Onboarding rápido y efectivo

**¡Comienza con `docs/CONTEXTO_PROYECTO.md`!** 🚀
