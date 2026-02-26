# **Guía Universal de Diagnóstico: Microservicios y Unidades Lógicas**
Este documento permite evaluar la calidad técnica tanto del "contenedor" (Microservicio) como del "contenido" (Unidades Lógicas) en entornos AWS.
## **1. Comparativa de Talla por Tipo de Cómputo (AWS)**

|**Característica**|**AWS Lambda (FaaS)**|**AWS ECS / Fargate (Contenedores)**|
| :- | :- | :- |
|**Propósito**|Tarea única, corta y específica.|Servicio de larga duración o API compleja.|
|**Puntos de Entrada**|1 (Trigger de evento/API).|5 - 15 (Múltiples endpoints REST).|
|**Tiempo de Vida**|Máximo 15 min (recomendado < 30s).|Indefinido.|
|**Carga de Memoria**|Muy sensible (afecta costo/velocidad).|Estable (según la reserva del clúster).|
## **2. Diagnóstico de la Unidad Lógica (Funciones y Métodos)**
### **Checklist de Salud de la Función**
1. **Atomicidad:** ¿Hace solo UNA cosa? Si usas la palabra "y" para describirla, divídela.
1. **Transparencia:** ¿Es una función pura? (Evitar efectos secundarios globales).
1. **Complejidad Cognitiva:**
   1. **Baja:** Lectura lineal.
   1. **Alta:** Muchos niveles de indentación (if anidados).
### **Métricas de la Unidad Lógica**
- **Largo de Función:** Máximo 30 líneas.
- **Nivel de Indentación:** Máximo 2 niveles.
- **Dependencias:** No más de 3 servicios/repositorios inyectados.
## **3. Consideraciones Específicas por Lenguaje**
Aquí es donde el diagnóstico se ajusta a la naturaleza del código fuente.
### **🐍 Python (Enfoque en Legibilidad y Agilidad)**
- **Type Hinting (Obligatorio):** Dado que Python es dinámico, el uso de *Type Hints* es crítico para que un programador nuevo entienda qué datos entran y salen sin ejecutar el código.
- **PEP 8:** El código debe seguir estrictamente el estándar de estilo.
- **Manejo de Cold Starts:** En Lambda, evitar importar librerías pesadas (como pandas o boto3) dentro del *handler*. Las importaciones deben ir fuera para aprovechar el reuso del contenedor.
- **Docstrings:** Uso de """ """ para explicar la intención de clases y módulos complejos.
### **☕ Java (Enfoque en Estructura y Rendimiento)**
- **Reducción de Boilerplate:** Uso de **Lombok** (@Data, @Builder) para mantener las clases de dominio limpias y cortas. Si una clase tiene 200 líneas de *getters* y *setters*, el diagnóstico de "talla" fallará injustamente.
- **Interfaces para desacoplamiento:** Es imperativo el uso de interfaces para la capa de infraestructura (DB, APIs externas) para facilitar el **Aislamiento** y las pruebas unitarias.
- **Optimización de Memoria (Lambda):** Si se usa Java en Lambda, evaluar **SnapStart** o **GraalVM (Native Image)**. Un microservicio Java que tarda 10 segundos en arrancar no es "saludable" para eventos en tiempo real.
- **Jerarquía de Excepciones:** No usar catch (Exception e). Se deben definir excepciones personalizadas (ej: PedidoNoEncontradoException).
## **4. Estándares de Nomenclatura (Naming)**

|**Tipo**|**Estándar**|**Ejemplo Bueno**|
| :- | :- | :- |
|**Microservicio**|[sistema]-[dominio]-[tipo]|crm-clientes-api|
|**Clase / Módulo**|Sustantivo, PascalCase|ProcesadorPagos|
|**Función**|Verbo, camelCase|obtenerHistorialPrecios()|
|**Variable Bool**|Prefijo de estado|estaHabilitado|
## **5. Estructura de "Caja Negra" Requerida**
Cada unidad lógica principal debe comportarse como una caja negra predecible:

1. **Entrada (Input):** Esquema validado (Pydantic en Python / DTOs con Validation API en Java).
1. **Proceso (Logic):** Lógica pura, sin credenciales quemadas (usar AWS Secrets Manager).
1. **Salida (Output):** Estructura estándar:\
   {\
   `  `"success": true,\
   `  `"data": { ... },\
   `  `"metadata": { "execution\_id": "uuid-123" }\
   }
## **6. El Diagnóstico de Mantenibilidad (Audit)**
Checklist para el programador con 2 años de experiencia:

- [ ] **Rastreo:** ¿Puedo seguir un error desde CloudWatch hasta la línea exacta?
- [ ] **Aislamiento:** ¿Puedo correr los tests sin conexión a internet/AWS?
- [ ] **Descubrimiento:** ¿El nombre de los archivos en src/ revela la funcionalidad?
- [ ] **Densidad de Comentarios:** ¿El código explica el "POR QUÉ" (decisiones de negocio) y no el "QUÉ"?
## **7. Arquitectura Sugerida**
- **Lambda:** Arquitectura de capas simple (Handler -> Service -> Repository).
- **ECS/Fargate:** **Arquitectura Hexagonal** (Puertos y Adaptadores) para proteger el dominio de cambios tecnológicos.
