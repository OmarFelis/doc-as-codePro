# **Estructura de Base de Datos para Auditoría de Microservicios**
Para centralizar el análisis de calidad, se propone una tabla en PostgreSQL (o similar con soporte JSONB) que permite almacenar tanto la metadata fija como los detalles técnicos variables de cada componente.
## **1. Diseño de la Tabla: quality\_audits**
Utilizaremos una sola tabla para ambos componentes (Microservicios y Unidades Lógicas) diferenciados por una columna entity\_type.

|**Columna**|**Tipo**|**Descripción**|
| :- | :- | :- |
|id|UUID (PK)|Identificador único de la auditoría.|
|parent\_id|UUID (FK)|ID del Microservicio al que pertenece (si la entidad es una Unidad Lógica).|
|entity\_name|VARCHAR|Nombre del componente (ej: pagos-api o calcular\_iva).|
|entity\_type|VARCHAR|MICROSERVICE o LOGIC\_UNIT.|
|runtime\_env|VARCHAR|LAMBDA, ECS\_FARGATE, K8S, etc.|
|language|VARCHAR|PYTHON, JAVA, NODEJS, etc.|
|risk\_level|VARCHAR|Nivel de criticidad: LOW, MEDIUM, HIGH.|
|overall\_score|DECIMAL|Puntaje de 0 a 100 basado en el cumplimiento.|
|description|**JSONB**|Propósito, "qué hace" y "por qué" (Metadata de negocio).|
|external\_relations|**JSONB**|Grafo de dependencias y comunicaciones externas.|
|metrics|**JSONB**|Datos cuantitativos (LOC, complejidad, endpoints).|
|compliance|**JSONB**|Checklist de cumplimiento (naming, layers, tests).|
|created\_at|TIMESTAMP|Fecha del diagnóstico.|
## **2. Estructura de los Campos JSONB**
### **A. Campo description (Contexto de Negocio)**
Este campo permite entender el impacto del componente sin leer el código.

{\
`  `"summary": "Maneja la lógica de procesamiento de pagos con tarjetas.",\
`  `"purpose": "Aislar la integración con procesadores externos del resto del sistema.",\
`  `"business\_value": "Garantiza la recaudación de ingresos de la plataforma.",\
`  `"owner\_team": "Fintech-Core",\
`  `"data\_sensitivity": "HIGH (PCI-DSS)"\
}
### **B. Campo external\_relations (Grafo de Dependencias)**
Define cómo se conecta este elemento con el ecosistema. Las relaciones mínimas deben ser:

{\
`  `"inbound": [\
`    `{ "source": "API Gateway", "protocol": "HTTPS", "type": "TRIGGER" },\
`    `{ "source": "orders-queue", "protocol": "SQS", "type": "EVENT" }\
`  `],\
`  `"outbound": [\
`    `{ "target": "stripe-api", "type": "EXTERNAL\_API" },\
`    `{ "target": "email-service", "type": "MICROSERVICE\_CALL" }\
`  `],\
`  `"data\_storage": [\
`    `{ "resource": "payments-db", "type": "DYNAMODB" },\
`    `{ "resource": "cache-cluster", "type": "REDIS" }\
`  `],\
`  `"events\_published": [\
`    `{ "topic": "payment-processed-event", "bus": "EventBridge" }\
`  `]\
}
### **C. Campo metrics (Cuantitativo)**
Varía según el tipo de entidad para capturar el "tamaño".

{\
`  `"lines\_of\_code": 1250,\
`  `"endpoint\_count": 8,\
`  `"cyclomatic\_complexity\_avg": 6.5,\
`  `"unit\_test\_coverage": 85.5\
}
## **3. Sentencia SQL de Creación (DDL)**
-- Definición de ENUM para riesgo si se prefiere tipado estricto\
CREATE TYPE risk\_level\_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH');\
\
CREATE TABLE quality\_audits (\
`    `id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),\
`    `parent\_id UUID REFERENCES quality\_audits(id) ON DELETE CASCADE,\
`    `entity\_name VARCHAR(255) NOT NULL,\
`    `entity\_type VARCHAR(50) CHECK (entity\_type IN ('MICROSERVICE', 'LOGIC\_UNIT')),\
`    `runtime\_env VARCHAR(50),\
`    `language VARCHAR(50),\
`    `risk\_level risk\_level\_enum DEFAULT 'MEDIUM',\
`    `overall\_score DECIMAL(5,2),\
`    `description JSONB NOT NULL DEFAULT '{}',\
`    `external\_relations JSONB NOT NULL DEFAULT '{}',\
`    `metrics JSONB NOT NULL DEFAULT '{}',\
`    `compliance JSONB NOT NULL DEFAULT '{}',\
`    `created\_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT\_TIMESTAMP\
);\
\
-- Índices optimizados\
CREATE INDEX idx\_audit\_entity ON quality\_audits (entity\_name, entity\_type);\
CREATE INDEX idx\_audit\_risk ON quality\_audits (risk\_level);\
-- Búsqueda por dependencias externas dentro del grafo\
CREATE INDEX idx\_audit\_relations ON quality\_audits USING GIN (external\_relations);
## **4. Ventajas del Nuevo Esquema**
1. **Gestión de Riesgos:** Permite priorizar refactorizaciones en componentes de riesgo HIGH con bajo overall\_score.
1. **Análisis de Impacto:** Mediante el grafo en external\_relations, se puede predecir qué otros servicios fallarán si un microservicio auditado tiene mala calidad.
1. **Diccionario de Servicios:** El campo description convierte esta tabla en un catálogo de servicios para nuevos desarrolladores.
