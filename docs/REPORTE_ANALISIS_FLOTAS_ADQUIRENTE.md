# Reporte de Análisis — FLOTAS-ADQUIRENTE

**Fecha:** 2026-02-26
**Herramienta:** doc-as-codePRO v3.0 — Fase 1
**Microservicio analizado:** `FLOTAS_ADQUIRENTE_DES`
**Stack:** Java + Struts MVC + Hibernate + JDBC directo

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos analizados | 131 |
| Líneas de código | 29,581 |
| Lenguajes | Java + JavaScript |
| Unidades lógicas detectadas | 725 |
| Overall Score | **71.64** |
| Risk general | **HIGH** |
| Unidades HIGH | 430 (59%) |
| Unidades con MULTICAPA | ~15 |

El score de 71.64 es aceptable para un sistema legacy Java/Struts. El risk HIGH elevado se explica principalmente por la alta complejidad ciclomática de las Actions de Struts, no necesariamente por mala arquitectura.

---

## Distribución por Capa

| Capa | Clases principales | Observación |
|------|--------------------|-------------|
| `[ADP]` Adaptador | `*Action` (Struts), `*Form`, `FiltroAutenticacion` | Correctamente identificadas como puntos de entrada HTTP |
| `[INF]` Infraestructura | `*Sql`, `HibernateSessionFactory`, `Conexion`, `*Entity` | Acceso a BD vía JDBC directo y Hibernate |
| `[DOM]` Dominio | `*Logic`, `Bean*`, `*Exception`, `utils/*` | Lógica de negocio, beans de datos, utilidades |

---

## Hallazgos Críticos — MULTICAPA

### CallCenterAction — `[INF][HIGH] score=56.4` ⚠️ MULTICAPA
```
CallCenterAction.enviarPOSVirtual
CallCenterAction.posVirtualExtorno
CallCenterAction.getNewOrderNumber
CallCenterAction.getFuelList
```
**Problema:** La Action de CallCenter mezcla lógica de presentación (Struts) con acceso directo a infraestructura (SQL/Hibernate). Debería delegar a la capa `logics/`. Es el patrón más riesgoso del proyecto.

### IssuerBinAction — `[INF][HIGH] score=56.9` ⚠️ MULTICAPA
```
IssuerBinAction.binCompanyRegistry
IssuerBinAction.obtenerBines
IssuerBinAction.eliminarBinCompany
```
**Problema:** Mismo patrón que CallCenterAction — Action que accede directamente a BD sin pasar por la capa de lógica.

---

## Hallazgos por Capa

### Capa Adaptador `[ADP]` — Actions de Struts

| Clase | Score | Observación |
|-------|-------|-------------|
| `CompanyAction` (9 métodos) | 56.6 | Gestión de empresas adquirentes. Alta complejidad esperada. |
| `LotsAction` (10 métodos) | 56.2 | Gestión de lotes de depósito. Score más bajo de las Actions. |
| `OrdersAction` (10 métodos) | 56.3 | Gestión de pedidos y consumos. |
| `EcommerceAction` (10+ métodos) | 56.2 | Gestión de comercios electrónicos. |
| `ReportsAction` (4 métodos) | 56.6 | Generación y descarga de reportes. |
| `PaginacionAction` (7 métodos) | 56.7 | Navegación entre tabs y paginación. |
| `UserAction` | ~56 | Gestión de usuarios del sistema. |

Todas las Actions tienen risk HIGH por complejidad ciclomática alta — es inherente al patrón Struts donde una Action maneja múltiples flujos con `getKeyMethodMap`.

### Capa Dominio `[DOM]` — Puntos positivos

| Clase | Score | Observación |
|-------|-------|-------------|
| `BeanFuel.*` getters/setters | 100.0 | Beans de datos perfectamente aislados. |
| `*Exception` (14 clases) | ~100.0 | Excepciones de negocio bien definidas y específicas. |
| `AdminAcquirerLogic` | ~70+ | Lógica de adquirente correctamente separada. |
| `AdminCompanyLogic` | ~70+ | Lógica de empresa en capa correcta. |
| `LogonLogic` | ~70+ | Lógica de autenticación separada de la Action. |

### Capa Infraestructura `[INF]`

| Clase | Score | Observación |
|-------|-------|-------------|
| `*Sql` (8 clases) | ~58 | JDBC directo: `AcquirerSql`, `CompanySql`, `EcommerceSql`, `LogonSql`, etc. Bien separados en su propia capa. |
| `HibernateSessionFactory` | ~70 | Factory de sesiones Hibernate. |
| `Conexion` | ~58 | Gestión de conexiones a BD. |
| `FuelEntity` / `ViewFuelEntity` | ~70 | Entidades Hibernate correctamente en infraestructura. |

---

## Observaciones sobre el Stack

**Struts MVC (no Spring):** El pipeline detectó correctamente el patrón Struts gracias a los imports `org.apache.struts`. Las Actions son adaptadores, no dominio.

**JDBC directo + Hibernate mixto:** El proyecto usa ambos — clases `*Sql` con JDBC puro y `*Entity` con Hibernate. Esto es deuda técnica de migración parcial.

**14 clases de excepción específicas:** Señal positiva — el dominio tiene excepciones bien tipadas (`CompanyRegisteredException`, `InvalidSessionException`, `LotEmptyException`, etc.), lo que indica que las reglas de negocio están modeladas.

**JavaScript legacy:** 16 archivos `.js` con error de parsing (`argument of type 'Module' is not iterable`) — son scripts jQuery/Struts de la época, el analizador JS no los soporta. No afecta el análisis Java.

---

## Recomendaciones

1. **Refactor prioritario:** `CallCenterAction` y `IssuerBinAction` — mover lógica de acceso a BD a clases `*Logic` o `*Sql` correspondientes. Son los únicos casos MULTICAPA reales.
2. **Unificar acceso a datos:** Decidir entre JDBC directo (`*Sql`) o Hibernate (`*Entity`) — actualmente coexisten ambos, lo que aumenta la complejidad de mantenimiento.
3. **Siguiente paso (Fase 2):** Activar extracción de reglas de negocio con LLM sobre `AdminAcquirerLogic`, `AdminCompanyLogic`, `LogonLogic` y las 14 excepciones de negocio — son los candidatos más valiosos para documentación automática.

---

*Generado por doc-as-codePRO v3.0 — Alignet Ecosistema de Pagos Digitales*
