# Reporte de Análisis — mvpRBAMOTORBACK

**Fecha:** 2026-02-26
**Herramienta:** doc-as-codePRO v3.0 — Fase 1
**Microservicio analizado:** `mvpRBAMOTORBACK`

---

## ¿Qué es una Unidad Lógica?

Una **unidad lógica** es la unidad mínima de análisis: cada función o método del código fuente.
El pipeline analiza cada función individualmente y le asigna:

- **Capa arquitectónica** — dónde vive en la arquitectura (ver abajo)
- **Score de calidad** — de 0 a 100, qué tan bien estructurada está
- **Risk level** — LOW / MEDIUM / HIGH, basado en el score y la complejidad

### Capas arquitectónicas

| Etiqueta | Nombre | Qué contiene |
|----------|--------|--------------|
| `[DOM]` | Dominio | Lógica de negocio pura: reglas, evaluadores, orquestadores, modelos de decisión. No depende de infraestructura. |
| `[INF]` | Infraestructura | Acceso a datos, BD, caché, servicios externos (Redis, PostgreSQL, APIs). Depende de tecnología concreta. |
| `[ADP]` | Adaptador | Puntos de entrada/salida: endpoints HTTP, tests de integración, CLI. Conecta el dominio con el mundo exterior. |

### Risk Level

| Nivel | Score | Significado |
|-------|-------|-------------|
| `[LOW]` | ≥ 70 | Código bien estructurado, bajo acoplamiento |
| `[MED]` | 40–69 | Complejidad moderada, revisar en próximo sprint |
| `[HIGH]` | < 40 o alta complejidad | Requiere atención: refactor, deuda técnica o lógica crítica sin suficiente separación |

### MULTICAPA

Marca que una función **mezcla responsabilidades de más de una capa** — por ejemplo, lógica de negocio dentro de una función que también accede a BD directamente. Es el principal indicador de acoplamiento indebido.

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos analizados | 72 |
| Líneas de código | 5,751 |
| Lenguaje | Python |
| Unidades lógicas detectadas | ~110 |
| Risk general | **HIGH** |

---

## Distribución por Capa

| Capa | Unidades | Observación |
|------|----------|-------------|
| `[DOM]` Dominio | ~65 | Mayoría del código. Contiene la lógica crítica de fraude y orquestación. |
| `[INF]` Infraestructura | ~25 | BD, contexto de stages, enriquecimiento de transacciones. |
| `[ADP]` Adaptador | ~20 | Tests de integración, endpoints de autenticación y reglas. |

---

## Hallazgos Críticos (HIGH)

### 1. TransactionEnricher — `[HIGH][INF] score=29.2` ⚠️ MULTICAPA
```
TransactionEnricher.enrich
TransactionEnricher._calculate_velocity
TransactionEnricher._enrich_device
TransactionEnricher._enrich_ip
TransactionEnricher._calculate_user_baseline
```
**Problema:** Score más bajo del proyecto (29.2). Mezcla enriquecimiento de datos con lógica de negocio (velocidad, baseline de usuario). Candidato prioritario a refactor — separar la lógica de cálculo en capa de dominio y dejar solo el acceso a datos en infraestructura.

---

### 2. Evaluadores de Stage — `[HIGH][DOM] score=56.6`
```
AutorizacionStageEvaluator  (5 métodos)
AutenticacionStageEvaluator (6 métodos)
PasarelaStageEvaluator      (6 métodos)
```
**Observación:** Clasificados correctamente como dominio. El score de 56.6 refleja alta complejidad inherente a las reglas de negocio (3DS, decisiones de autorización, recomendaciones). No es deuda técnica — es complejidad de negocio esperada. Candidatos a documentación con LLM en Fase 2.

---

### 3. HybridOrchestrator — `[HIGH][DOM] score=68.5`
```
HybridOrchestrator (6 métodos)
```
**Observación:** Orquestador que combina ML + reglas. Score de 68.5 es aceptable para su responsabilidad. El risk HIGH se debe a la cantidad de dependencias que maneja, no a mala estructura.

---

### 4. Scripts de demo clasificados como HIGH
```
test_different_strategies  score=57.2  [HIGH][DOM]
print_header / print_result / test_scenario
```
**Observación:** Son funciones de scripts de prueba/demo que el pipeline clasifica como dominio porque no tienen imports de infraestructura. Recomendación: mover a un directorio `scripts/` o `demos/` y agregarlo a `IGNORED_FOLDERS`.

---

## Hallazgos Medios (MEDIUM)

| Unidad | Score | Observación |
|--------|-------|-------------|
| `StageContextManager` (6 métodos) | 41.7 | Gestión de contexto de stages con acceso a BD. Score bajo — revisar si puede simplificarse. |
| `RulesEngine` (4 métodos) | 69.3 | Motor de reglas bien estructurado, cerca del umbral LOW. |
| `main` | 41.7 | Función de entrada con demasiada responsabilidad. |
| `check_file / check_module` | 41.7 | Funciones de validación con lógica mezclada. |

---

## Puntos Positivos

| Unidad | Score | Observación |
|--------|-------|-------------|
| `get_settings` | 100.0 | Configuración perfectamente aislada. |
| `FraudPredictor` | 84.0 | Predictor ML bien encapsulado en dominio. |
| `IPEnricher` / `FeatureEngineer` | 82.9 | Buena separación de responsabilidades. |
| `DecisionOrchestrator` | 83.3 | Orquestador de decisiones limpio. |
| Tests `[ADP]` | ~67–68 | Tests de integración correctamente clasificados como adaptadores. |

---

## Recomendaciones

1. **Refactor prioritario:** `TransactionEnricher` — extraer `_calculate_velocity` y `_calculate_user_baseline` a capa de dominio.
2. **Agregar a IGNORED_FOLDERS:** directorio `scripts/` o `demos/` para evitar que funciones de prueba contaminen el análisis.
3. **Siguiente paso (Fase 2):** Activar extracción de reglas de negocio con LLM sobre los evaluadores de stage (`AutorizacionStageEvaluator`, `AutenticacionStageEvaluator`, `PasarelaStageEvaluator`) — son los candidatos más valiosos para documentación automática.

---

*Generado por doc-as-codePRO v3.0 — Alignet Ecosistema de Pagos Digitales*
