# **🏛️ INI: Code-Agent V1.0**
## **1. Información General**
- **1.1 Título (Summary):** Agente Inteligente para el Mapeo y Documentación Automatizada de Arquitectura Técnica (Code-Intelligence).
- **1.2 Sponsor / PO:** Javier Draxl.
- **1.3 Tipo / Estado:** Iniciativa Estratégica / En Evaluación de Impacto.
## **2. Descripción y Contexto (El Qué y el Por qué ahora)**
- **2.1 Descripción:** Implementación de un ecosistema de IA que realiza ingeniería inversa de microservicios (Lambdas y otros componentes) para mapear funciones, flujos lógicos y reglas de negocio en una base de datos de grafos estructurada. El sistema actúa como una "Fuente de la Verdad" técnica que permite a POs, analistas y desarrolladores consultar la arquitectura y el impacto de cambios mediante lenguaje natural y visualización granular.
- **2.2 Contexto:** Actualmente se cuenta con un piloto que genera documentación en Confluence, los resultados son documentos completos pero extensos y no estructurados que hacen difícil consumo por parte de los usuarios.
  - **El Problema:** Existe una falta de visibilidad directa e inmediata sobre el detalle interno (funciones y flujos) de microservicios críticos que deben ser refactorizados. El usuario debe conocer el nombre de cada microservicio, buscarlo en Confluence y leer todo el documento para un entendimiento general para un cambio específico. No están vinculados ni relacionados con otros componentes.
  - **El Riesgo:** El crecimiento del código impulsado por IA será exponencial en los próximos meses. Sin una herramienta que mapee este crecimiento en tiempo real y lo disponga de manera esquemática a los usuarios, la arquitectura se volverá inmanejable ("ingobernable"), aumentando la dependencia de conocimiento humano que es difícil de sostener y escalar. Muy pocas personas podrán entender todo el código que se genere.
## **3. Beneficio (Valor cualitativo)**
- **3.1 Para el Colaborador Interno (PO/Analista):** Análisis de impacto inmediato durante el *Discovery* de Historias de Usuario (HU). "Paz mental" al validar cambios sin depender de la disponibilidad de un desarrollador.
- **3.2 Para el Desarrollador:** Acceso a una "radiografía" exacta del código y sugerencias proactivas de refactorización basadas en métricas de complejidad.
- **3.3 Para la Organización:** Reducción drástica del *Time-to-Market* y mitigación de riesgos operativos en sistemas core (ACS, Orquestador).
- **3.4 Visualización:** El diagramador visual desarrollado alcanza un nivel de detalle que facilita el entendimiento técnico a perfiles no técnicos.
- **3.5 Visión de Futuro:** Establecimiento de una simetría de lenguaje entre agentes de IA y analistas humanos, manteniendo siempre al humano "en el loop" de las decisiones de cambio.
## **4. Objetivo (Metas SMART)**
- **4.1 Eficiencia Operativa:** Reducir el tiempo de análisis de impacto de una HU compleja de **4 horas a 30 minutos** mediante el uso del agente.
- **4.2 Cobertura Crítica:** Lograr el **100% de mapeo y documentación** de las aplicaciones: **ACS, Orquestador, PSE, OSE y Transaction Key** para el **14 de marzo**.
- **4.3 Integridad Técnica:** Implementar la capacidad de comparación de diferencias arquitectónicas entre los ambientes de **QA y DEV** para el **15 de abril**.
## **5. Propósito (Alineación Estratégica)**
Democratizar el conocimiento técnico profundo para permitir que la organización escale su complejidad tecnológica sin perder agilidad, asegurando que cada línea de código sea entendida y mantenida bajo estándares de alta calidad.
## **6. Impacto (Valor cuantitativo)**
- **6.1 Capacidad de Equipo:** Liberación de aproximadamente 3.5 horas de análisis técnico por cada HU compleja, permitiendo mayor foco en el diseño de producto.
- **6.2 Reducción de Errores:** Mitigación de fallos en producción derivados de "impactos invisibles" en microservicios interconectados.
## **7. Atributos de Calidad (NFRs)**
- **7.1 Seguridad:** Operación 100% local dentro de la red. Acceso de **Solo Lectura** a repositorios (GitHub/Bitbucket). No accede a producción.
- **7.2 Mantenibilidad (Política de Referencia):** El agente auditará el código bajo estas métricas:
  - **Complejidad Ciclomática:** Ideal 1-10. Si es > 15, se marca para refactorización.
  - **Líneas de Código (LoC):** Rango de 500 a 2,000 por microservicio.
  - **Tiempo de Despliegue:** < 5 minutos.
  - **Cobertura de Tests:** > 80% obligatorio.
- **7.3 Disponibilidad:** Fase 1 bajo demanda; no requiere HA 24/7.
## **8. Impacto de No Hacerlo (Costo de Inacción)**
Si no se implementa, los sistemas alcanzarán la ingobernabilidad técnica. La deuda técnica acumulada y la velocidad de la IA generativa crearán silos de código que nadie podrá explicar, paralizando la innovación y aumentando el riesgo de caídas sistémicas ante cualquier cambio en el Orquestador o ACS.
## **9. Requerimientos Funcionales**
- **9.1 Resumen y Vinculación:** Generar resúmenes funcionales y vincularlos automáticamente al grafo de la aplicación.
- **9.2 Gestión de Activos (Asset Management):** Cada unidad (Función, Flujo o Detalle) es un registro independiente en la **BD Postgres de A-ONE**.
  - Tipos de activos: UNIDAD\_LOGICA\_FLUJO, UNIDAD\_LOGICA\_FUNCION, UNIDAD\_LOGICA\_DETALLE, UNIDAD\_LOGICA\_REGLA\_NEGOCIO.
  - Cada activo tiene atributos estándar de la capa a la que pertenece según la **Tabla de Parámetros Maestro**.
- **9.3 Auditoría de Arquitectura de Capas:** El agente verificará la separación estricta:
  - **Adaptadores (Entrada):** Sin lógica de negocio.
  - **Dominio (Lógica):** Código puro, agnóstico de infraestructura.
  - **Infraestructura (Salida):** Llamadas a BD o AWS.
- **9.4 Extracción y Registro de Reglas de Negocio:** Identificar y registrar en lenguaje natural las validaciones y cálculos del Dominio. Estas reglas deben ser guardadas en la base de datos de registro de reglas de negocio (conocimiento\_organizacional) y estar vinculadas obligatoriamente con la **Aplicación**, el **Componente** y la **Unidad Lógica** correspondiente para asegurar trazabilidad total.
- **9.5 Mapeo de Infraestructura:** Relaciones REL-INFRA vinculando código con componentes AWS (S3, SQS, Dynamo).
- **9.6 Unidades Multicapa:** Identificar y marcar con bandera de riesgo cualquier activo que pertenezca a más de una capa (Acoplamiento).
## **10. No Incluye (Fuera de Alcance)**
- **10.1 Fase 1:** No incluye integración automática en CI/CD ni escritura/edición de código en repositorios.
## **11. Stakeholders y Personas**
- **11.1 Analista/PO:** Sufre por la dependencia de expertos para el Discovery. Busca "paz mental" y autonomía técnica.
- **11.2 Dev Senior / Arquitecto:** Requiere herramientas para refactorizar sin miedo a romper flujos invisibles.
## **12. Supuestos y Restricciones**
- **12.1 Restricciones:** Ejecución en entorno aislado. Sin salida a internet.
- **12.2 Supuestos:** TI otorgará los permisos de lectura necesarios en los plazos definidos.
## **13. Riesgos**
- **13.1 Alucinación de IA:** Entrega de información errónea. *Mitigación:* Validación humana obligatoria.
- **13.2 Visión Limitada:** Dependencias AWS no declaradas en código. *Mitigación:* Mapeo manual complementario en grafo.
## **14. Anexo: Guía de Tallas y Diagnóstico**
- **14.1 Diagnóstico de Tamaño:** Un microservicio es demasiado grande si:
  - ¿Usa la palabra "y" para explicar su función? (Ej: Gestiona pagos y facturas).
  - ¿Al cambiar una función, rompe algo no relacionado?
  - ¿Tarda el equipo más de una semana en entenderlo?
- **14.2 Lambda-litos:** Prohibición de Lambdas con lógica ramificada masiva (switches gigantes). Una Lambda = Una tarea.

**Barómetro de Madurez: 100%**
