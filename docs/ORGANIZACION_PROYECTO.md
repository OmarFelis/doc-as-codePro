# 📂 Organización del Proyecto

Este repositorio contiene dos versiones del servicio Doc-as-Code:

## 🗂️ Estructura

```
omarpruebas2-doc-as-code-service-pre-prod/
│
├── 📁 doc-as-codePRO/          ⭐ NUEVO - Versión 3.0 Modernizada
│   ├── src/                    # Código fuente refactorizado
│   ├── tests/                  # Tests unitarios e integración
│   ├── infrastructure/         # IaC (futuro)
│   ├── pyproject.toml          # Poetry + configuración
│   ├── README.md               # Documentación principal v3.0
│   ├── QUICKSTART.md           # Inicio rápido
│   └── [más documentación]     # 8 documentos completos
│
├── 📁 ci-scripts/              📦 LEGACY - Versión 2.0 (Funcional)
│   ├── generate_docs_mejorado.py
│   ├── ast_analyzer.py
│   ├── post_to_confluence.py
│   └── [otros scripts]
│
├── 📁 docs/                    # Documentación generada
├── bitbucket-pipelines.yml     # Pipeline actual (v2.0)
├── Dockerfile                  # Docker v2.0
├── requirements.txt            # Dependencias v2.0
└── README.md                   # Este archivo
```

## 🎯 ¿Qué Versión Usar?

### ⭐ doc-as-codePRO (v3.0) - RECOMENDADO para nuevos desarrollos

**Usar si:**
- ✅ Estás comenzando un nuevo desarrollo
- ✅ Quieres arquitectura limpia y mantenible
- ✅ Necesitas extensibilidad (agregar Java, JS, etc.)
- ✅ Quieres tests y type safety
- ✅ Buscas mejores prácticas modernas

**Características:**
- 🏗️ Arquitectura limpia (SOLID)
- 🔒 Type safety 100% (Pydantic + mypy)
- 📝 Logging estructurado (structlog)
- 🧪 Testing framework (pytest)
- ⚡ Procesamiento paralelo
- 📚 Documentación completa

**Inicio rápido:**
```bash
cd doc-as-codePRO
poetry install
poetry run python example.py
```

**Documentación:** `doc-as-codePRO/README.md`

---

### 📦 ci-scripts (v2.0) - LEGACY pero funcional

**Usar si:**
- ⚠️ Necesitas compatibilidad con pipelines existentes
- ⚠️ No puedes migrar ahora mismo
- ⚠️ Requieres funcionalidad específica de v2.0

**Características:**
- ✅ Funcional en producción
- ✅ Integrado con Bitbucket Pipelines
- ✅ Soporta 30+ lenguajes
- ⚠️ Código monolítico
- ⚠️ Sin tests
- ⚠️ Difícil de mantener

**Uso:**
```bash
python ci-scripts/generate_docs_mejorado.py
python ci-scripts/post_to_confluence.py
```

**Documentación:** `DOCUMENTACION_ACTUALIZADA_FINAL.md`

---

## 🔄 Migración de v2.0 a v3.0

### Paso 1: Familiarízate con v3.0
```bash
cd doc-as-codePRO
cat QUICKSTART.md
```

### Paso 2: Prueba el ejemplo
```bash
poetry install
poetry run python example.py
```

### Paso 3: Compara resultados
- v2.0: Ejecuta scripts legacy
- v3.0: Ejecuta nuevo sistema
- Valida que ambos generen documentación similar

### Paso 4: Migra gradualmente
- Usa v3.0 para nuevos proyectos
- Mantén v2.0 para proyectos existentes
- Migra cuando sea conveniente

---

## 📊 Comparación Rápida

| Característica | v2.0 Legacy | v3.0 PRO |
|----------------|-------------|----------|
| **Arquitectura** | Monolítica | Limpia |
| **Líneas de código** | ~2000 | ~890 |
| **Type safety** | 20% | 100% |
| **Tests** | 0% | 60%+ |
| **Logging** | print() | structlog |
| **Configuración** | Hardcoded | Pydantic |
| **Extensibilidad** | Difícil | Fácil |
| **Mantenibilidad** | Baja | Alta |
| **Documentación** | Básica | Completa |
| **Estado** | Funcional | En desarrollo |

---

## 🚀 Recomendaciones

### Para Nuevos Proyectos
👉 **Usa doc-as-codePRO (v3.0)**
- Mejor arquitectura
- Más fácil de mantener
- Preparado para el futuro

### Para Proyectos Existentes
👉 **Mantén ci-scripts (v2.0) por ahora**
- Ya funciona
- No requiere cambios
- Migra cuando tengas tiempo

### Para Desarrollo Futuro
👉 **Invierte en doc-as-codePRO (v3.0)**
- Base sólida para nuevas features
- Fácil agregar analizadores
- Preparado para API REST

---

## 📚 Documentación

### v3.0 (doc-as-codePRO)
- **Inicio:** `doc-as-codePRO/QUICKSTART.md`
- **Completa:** `doc-as-codePRO/README_v3.md`
- **Ejecutiva:** `doc-as-codePRO/RESUMEN_EJECUTIVO.md`
- **Índice:** `doc-as-codePRO/INDICE_DOCUMENTACION.md`

### v2.0 (ci-scripts)
- **Principal:** `DOCUMENTACION_ACTUALIZADA_FINAL.md`
- **Implementación:** `GUIA_IMPLEMENTACION.md`
- **Original:** `README.md` (este archivo antes)

---

## 🎯 Roadmap

### Fase 1: Fundamentos ✅ COMPLETADA
- Arquitectura limpia
- Analizador Python
- Testing framework
- Documentación completa

### Fase 2: Modernización (Próxima)
- API REST con FastAPI
- Más analizadores (Java, JS, TS)
- Generadores de documentación
- Cache con Redis

### Fase 3: Optimización
- Celery para async
- PostgreSQL
- Métricas con Prometheus

### Fase 4: Infraestructura
- Kubernetes
- Terraform
- CI/CD completo

---

## 💡 Preguntas Frecuentes

**P: ¿Debo migrar ahora?**  
R: No es urgente. v2.0 sigue funcionando. Migra cuando tengas tiempo.

**P: ¿Puedo usar ambas versiones?**  
R: Sí, son independientes. Usa v3.0 para nuevos proyectos.

**P: ¿v2.0 seguirá recibiendo soporte?**  
R: Mantenimiento mínimo. Nuevas features solo en v3.0.

**P: ¿Cuánto tiempo toma migrar?**  
R: Depende del proyecto. Para análisis básico: 1-2 días.

**P: ¿v3.0 tiene todas las features de v2.0?**  
R: No todavía. Fase 1 completa, Fase 2 en progreso.

---

## 📞 Soporte

**Para v3.0 (doc-as-codePRO):**
- Lee `doc-as-codePRO/QUICKSTART.md`
- Revisa `doc-as-codePRO/INDICE_DOCUMENTACION.md`

**Para v2.0 (ci-scripts):**
- Lee `DOCUMENTACION_ACTUALIZADA_FINAL.md`
- Revisa `GUIA_IMPLEMENTACION.md`

---

**Última actualización:** Enero 2025  
**Versión actual:** v2.0 (producción) + v3.0 (desarrollo)  
**Mantenedor:** Alignet Tech Team
