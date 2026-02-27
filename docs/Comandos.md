# Comandos del Proyecto - doc-as-codePRO v3.0

## Instalación

```bash
# Instalar dependencias
poetry install

# Instalar con grupos de desarrollo
poetry install --with dev

# Instalar pre-commit hooks
poetry run pre-commit install
```

## Servidor API

```bash
# Levantar servidor de desarrollo
poetry run uvicorn src.api.main:app --reload

# Levantar en puerto específico
poetry run uvicorn src.api.main:app --reload --port 8080

# Levantar con host expuesto
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```bash
# Ejecutar todos los tests
poetry run pytest

# Tests con reporte de cobertura en terminal
poetry run pytest --cov=src --cov-report=term-missing

# Tests con reporte HTML (genera htmlcov/)
poetry run pytest --cov=src --cov-report=html

# Ejecutar un archivo de test específico
poetry run pytest tests/unit/test_paso1_smoke.py

# Ejecutar tests por nombre
poetry run pytest -k "test_java"

# Tests con output verbose
poetry run pytest -v

# Tests sin captura de output (ver prints)
poetry run pytest -s

# Ejecutar tests de integración
poetry run pytest tests/integration/

# Ejecutar tests unitarios
poetry run pytest tests/unit/

# Test de fase 1 completa
poetry run pytest tests/test_fase1_casos_prueba.py -v
```

## Scripts de Ejemplo y Demo

```bash
# Ejecutar ejemplo principal
poetry run python example.py

# Demo de fase 1 — corre todos los fixtures
poetry run python demo_fase1.py

# Demo con fixture específico (dominio_puro | multicapa | infraestructura | alta_complejidad | todos)
poetry run python demo_fase1.py --fixture dominio_puro

# Demo contra una ruta real del sistema de archivos
poetry run python demo_fase1.py --path C:/repos/mi-microservicio

# Demo contra ruta real con nombre personalizado, guardando output en archivo
poetry run python demo_fase1.py --path C:/repos/mi-microservicio --name MiServicio > output.txt

# Demo contra ruta real guardando output (ejemplo con Java)
poetry run python demo_fase1.py --path C:/repos/mi-servicio-java --name ServicioJava > output_java.txt

# Análisis personalizado
poetry run python analyze_custom.py

# Debug de análisis
poetry run python debug_analyze.py

# Test de API (requiere servidor corriendo)
poetry run python test_api.py

# Test multi-lenguaje API (requiere servidor corriendo)
poetry run python test_multi_language_api.py
```

## Calidad de Código

```bash
# Formatear código con black
poetry run black src/ tests/

# Verificar formato sin aplicar
poetry run black src/ tests/ --check

# Linting con ruff
poetry run ruff check src/ tests/

# Linting con auto-fix
poetry run ruff check src/ tests/ --fix

# Type checking con mypy
poetry run mypy src/

# Ejecutar todos los checks de pre-commit
poetry run pre-commit run --all-files
```

## Base de Datos (Alembic)

```bash
# Crear nueva migración
poetry run alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
poetry run alembic upgrade head

# Revertir última migración
poetry run alembic downgrade -1

# Ver historial de migraciones
poetry run alembic history
```

## Endpoints API (con servidor corriendo en localhost:8000)

```bash
# Health check
curl http://localhost:8000/health

# Documentación interactiva
# Abrir en browser: http://localhost:8000/docs

# Analizar código (ejemplo)
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"path": "./examples/sample_java"}'
```

## Gestión de Dependencias

```bash
# Ver dependencias instaladas
poetry show

# Agregar nueva dependencia
poetry add <paquete>

# Agregar dependencia de desarrollo
poetry add --group dev <paquete>

# Actualizar dependencias
poetry update

# Exportar requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
