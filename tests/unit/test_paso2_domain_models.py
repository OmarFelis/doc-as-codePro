"""Paso 2 — Tests de modelos de dominio nuevos (ArchivoFuente, UnidadLogica, Escaneo, enums)."""
from src.models.domain import (
    TipoUnidad, RiskLevel, ArchitectureLayer,
    ArchivoFuente, UnidadLogica, Escaneo, BusinessRule,
)

ACTIVO_ID = "00000000-0000-0000-0000-000000000001"


def test_tipo_unidad_values():
    assert TipoUnidad.CLASE == "CLASE"
    assert TipoUnidad.FUNCION == "FUNCION"
    assert TipoUnidad.INTERFAZ == "INTERFAZ"
    assert TipoUnidad.ENUM == "ENUM"


def test_risk_level_values():
    assert RiskLevel.LOW == "LOW"
    assert RiskLevel.MEDIUM == "MEDIUM"
    assert RiskLevel.HIGH == "HIGH"


def test_architecture_layer_values():
    assert ArchitectureLayer.ADAPTADOR == "adaptador"
    assert ArchitectureLayer.DOMINIO == "dominio"
    assert ArchitectureLayer.INFRAESTRUCTURA == "infraestructura"


def test_archivo_fuente_minimal():
    a = ArchivoFuente(activo_id=ACTIVO_ID, nombre="payments.py", ruta_archivo="src/payments.py")
    assert a.nombre == "payments.py"
    assert a.activo_id == ACTIVO_ID
    assert a.id is None
    assert a.total_funciones == 0
    assert a.endpoints == []


def test_archivo_fuente_completo():
    a = ArchivoFuente(
        activo_id=ACTIVO_ID,
        nombre="adapter.py",
        ruta_archivo="src/adapter.py",
        capa="adaptador",
        lenguaje="python",
        total_funciones=3,
        total_clases=1,
        complejidad_ciclomatica=5,
        lineas_codigo=80,
    )
    assert a.capa == "adaptador"
    assert a.total_funciones == 3
    assert a.lineas_codigo == 80


def test_unidad_logica_clase():
    u = UnidadLogica(activo_id=ACTIVO_ID, nombre="MiClase", tipo=TipoUnidad.CLASE)
    assert u.tipo == "CLASE"
    assert u.parent_id is None
    assert u.risk_level == "MEDIUM"
    assert u.compliance == {}


def test_unidad_logica_funcion_con_parent():
    u = UnidadLogica(
        activo_id=ACTIVO_ID,
        nombre="calcular_iva",
        tipo=TipoUnidad.FUNCION,
        parent_id="uuid-clase",
        capa="dominio",
        risk_level=RiskLevel.HIGH,
        overall_score=42.5,
        compliance={"has_multi_layer_coupling": True},
    )
    assert u.parent_id == "uuid-clase"
    assert u.risk_level == "HIGH"
    assert u.overall_score == 42.5
    assert u.compliance["has_multi_layer_coupling"] is True


def test_escaneo_minimal():
    e = Escaneo(activo_id=ACTIVO_ID)
    assert e.activo_id == ACTIVO_ID
    assert e.id is None
    assert e.archivos_total == 0
    assert e.negocio == {}


def test_escaneo_con_metricas():
    e = Escaneo(
        activo_id=ACTIVO_ID,
        score_general=66.4,
        nivel_riesgo=RiskLevel.HIGH,
        archivos_total=72,
        funciones_total=116,
        clases_total=28,
    )
    assert e.score_general == 66.4
    assert e.nivel_riesgo == "HIGH"
    assert e.funciones_total == 116


def test_business_rule_fields():
    rule = BusinessRule(
        description="Valida que el monto sea mayor a cero antes de procesar el pago",
        linked_application="ACS",
        linked_component="payments.py",
        linked_unit_name="procesar_pago",
    )
    assert rule.linked_application == "ACS"
    assert rule.linked_unit_name == "procesar_pago"
    assert "monto" in rule.description
