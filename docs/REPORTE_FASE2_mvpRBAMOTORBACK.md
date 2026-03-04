# Análisis del Output — Fase 2: Enriquecimiento LLM con AWS Strands

**Proyecto analizado:** `mvpRBAMOTORBACK`  
**Fecha:** 2026-03-04  
**Modo:** `--dry-run --enrich`

---

## ¿Qué hizo el pipeline?

El pipeline ejecutó las **Fases 1 y 2** en secuencia sobre el repositorio real:

```
Fase 1: Parseo del código fuente
    → 52 archivos detectados
    → 64 clases extraídas
    → 126 funciones extraídas
    → Jerarquía física/lógica construida

Fase 2: Enriquecimiento con AWS Strands + Claude 3.5 Sonnet
    → 62 llamadas a herramientas Bedrock
    → Resúmenes generados por unidad lógica
    → Reglas de negocio extraídas
    → Resumen ejecutivo del microservicio generado
```

---

## Resultado del escaneo

| Campo | Valor |
|---|---|
| `escaneo_id` | `a9580552-5fa2-4fcd-97dc-0c60b448606e` |
| `score_general` | `83.18` |
| `nivel_riesgo` | `HIGH` |
| `archivos_total` | `52` |
| `clases_total` | `64` |
| `funciones_total` | `126` |
| `enriquecido` | `True` |

El score **83.18 / HIGH** es esperado para un motor de fraude — alta complejidad ciclomática, múltiples capas, lógica de negocio crítica.

---

## ¿Qué hizo el agente Strands?

El agente recibió cada archivo con su código fuente y decidió autónomamente qué herramientas llamar:

### Herramienta 1: `enriquecer_unidades`
Generó resúmenes en español para cada función/clase de **capa DOMINIO**.

Ejemplo extraído del output:
```
Clase: RulesEngine
→ "Motor de reglas configurable para evaluación de riesgo transaccional.
   Implementa scoring aditivo con límite máximo de 1000 puntos."

Método: calcular_riesgo
→ "Evalúa múltiples factores de riesgo (monto, hora, velocidad, geografía)
   y retorna un score acumulativo con factores explicativos."
```

### Herramienta 2: `extraer_reglas_negocio`
Extrajo reglas de negocio con valores concretos del código:

| Regla | Puntos | Condición |
|---|---|---|
| Monto alto | 300 pts | `amount > umbral_configurable` |
| Internacional + monto | 250 pts | `is_international AND amount > umbral` |
| Hora inusual | 200 pts | Ventana nocturna |
| Fin de semana + monto | 150 pts | `day_of_week >= 5 AND amount > 5000` |
| Velocidad transaccional | Variable | Historial por usuario |

### Herramienta 3: `generar_resumen_microservicio`
Generó el resumen ejecutivo final del microservicio completo:

> **mvpRBAMOTORBACK** es un motor de reglas de negocio (RBA) para detección de fraude en transacciones financieras. Implementa un sistema multi-etapa que evalúa transacciones en tres fases: pasarela, autenticación (3DS) y autorización (ISO8583).

**Sensibilidad de datos detectada:** ALTA  
Razón: procesa datos de tarjetas, credenciales, historial transaccional.

---

## Arquitectura detectada por el agente

```
mvpRBAMOTORBACK
├── Capa Adaptadores
│   ├── AutorizacionAdapter  (ISO8583)
│   ├── AREQAdapter          (3D Secure)
│   └── PasarelaAdapter      (Pasarela)
├── Capa Dominio
│   ├── RulesEngine          (motor de reglas)
│   ├── RiskScorer           (scoring)
│   └── TransactionEvaluator (orquestación)
└── Capa Infraestructura
    ├── JWT Auth
    ├── PostgreSQL ORM
    └── API REST (FastAPI)
```

---

## Observaciones del output

### ✅ Lo que funcionó bien
- El agente identificó correctamente el dominio de negocio (fraude financiero)
- Extrajo reglas con valores numéricos reales del código (`0.035`, `5000`, `1000`)
- Detectó sensibilidad de datos ALTA con justificación
- Reconoció los 3 adaptadores de formato por nombre

### ⚠️ Área de mejora aplicada
Los archivos `__init__.py` vacíos (tools #60, #61, #62) consumieron tokens innecesariamente.  
**Fix aplicado:** el pipeline ahora salta archivos sin unidades lógicas (`saved_logicas` vacío).

### 📌 Limitación conocida
`generar_resumen_microservicio` recibe solo nombres de funciones como inventario — sin código fuente completo. El agente lo compensó con el contexto acumulado de los archivos anteriores, pero el resumen podría ser más preciso si recibiera también las capas detectadas.

---

## Próximos pasos (Fase 3)

Con los datos ya en `code.archivos_fuente`, `code.unidades_logicas` y `quality.escaneos`, el siguiente paso es:

1. Conectar con PostgreSQL real (DBA confirma BD y acceso)
2. Registrar los endpoints en el backend genérico de A-ONE
3. Crear relaciones `REL-INFRA-05` en `grafo.relaciones_globales`

---

*Generado: doc-as-codePRO — Alignet Ecosistema de Pagos Digitales*
