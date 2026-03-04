"""Paso 3 — Tests del LogicalUnitExtractor (nuevo modelo ArchivoFuente + UnidadLogica)."""
import pytest
from src.models.domain import FileAnalysis, LanguageType, ArchivoFuente, UnidadLogica
from src.core.analyzers.logical_unit_extractor import extract, _classify_layer, _has_multi_layer_coupling

ACTIVO_ID = "00000000-0000-0000-0000-000000000001"


def _make_analysis(**kwargs) -> FileAnalysis:
    defaults = dict(
        file_path="payments.py",
        language=LanguageType.PYTHON,
        lines=50,
        functions=["calcular_comision", "validar_monto"],
        imports=[],
        database_calls=[],
        complexity=5,
        classes=[],
    )
    defaults.update(kwargs)
    return FileAnalysis(**defaults)


# --- Clasificación de capas ---

def test_layer_adaptador():
    assert _classify_layer(["fastapi", "pydantic"]).value == "adaptador"

def test_layer_infraestructura_boto3():
    assert _classify_layer(["boto3", "json"]).value == "infraestructura"

def test_layer_infraestructura_sqlalchemy():
    assert _classify_layer(["sqlalchemy.orm", "os"]).value == "infraestructura"

def test_layer_dominio_sin_imports():
    assert _classify_layer([]).value == "dominio"

def test_layer_dominio_imports_puros():
    assert _classify_layer(["datetime", "decimal", "typing"]).value == "dominio"


# --- Multi-layer coupling ---

def test_multi_layer_coupling_detectado():
    assert _has_multi_layer_coupling(["fastapi", "boto3"]) is True

def test_multi_layer_coupling_no_detectado():
    assert _has_multi_layer_coupling(["fastapi"]) is False
    assert _has_multi_layer_coupling(["boto3"]) is False
    assert _has_multi_layer_coupling([]) is False


# --- Producción de ArchivoFuente + UnidadLogica ---

def test_extract_retorna_archivo_y_unidades():
    archivo, unidades = extract(_make_analysis(), ACTIVO_ID)
    assert isinstance(archivo, ArchivoFuente)
    assert isinstance(unidades, list)

def test_extract_archivo_nombre_correcto():
    archivo, _ = extract(_make_analysis(file_path="src/payments.py"), ACTIVO_ID)
    assert archivo.nombre == "payments.py"

def test_extract_archivo_activo_id():
    archivo, _ = extract(_make_analysis(), ACTIVO_ID)
    assert archivo.activo_id == ACTIVO_ID

def test_extract_produce_una_unidad_por_funcion():
    fa = _make_analysis(functions=["f1", "f2", "f3"])
    _, unidades = extract(fa, ACTIVO_ID)
    funciones = [u for u in unidades if u.tipo == "FUNCION"]
    assert len(funciones) == 3

def test_extract_clase_tiene_parent_id_none():
    fa = _make_analysis(classes=["MiClase"], functions=[])
    _, unidades = extract(fa, ACTIVO_ID)
    clases = [u for u in unidades if u.tipo == "CLASE"]
    assert len(clases) == 1
    assert clases[0].parent_id is None

def test_extract_metodo_tiene_parent_id_de_su_clase():
    fa = _make_analysis(classes=["MiClase"], functions=["MiClase.mi_metodo"])
    _, unidades = extract(fa, ACTIVO_ID)
    clase = next(u for u in unidades if u.tipo == "CLASE")
    metodo = next(u for u in unidades if u.tipo == "FUNCION")
    assert metodo.parent_id == clase.id

def test_extract_funcion_standalone_tiene_parent_id_none():
    fa = _make_analysis(classes=[], functions=["standalone_func"])
    _, unidades = extract(fa, ACTIVO_ID)
    assert unidades[0].parent_id is None

def test_extract_risk_low():
    _, unidades = extract(_make_analysis(complexity=5), ACTIVO_ID)
    assert all(u.risk_level == "LOW" for u in unidades)

def test_extract_risk_medium():
    _, unidades = extract(_make_analysis(complexity=12), ACTIVO_ID)
    assert all(u.risk_level == "MEDIUM" for u in unidades)

def test_extract_risk_high():
    _, unidades = extract(_make_analysis(complexity=16), ACTIVO_ID)
    assert all(u.risk_level == "HIGH" for u in unidades)

def test_extract_overall_score_calculado():
    _, unidades = extract(_make_analysis(), ACTIVO_ID)
    assert all(u.overall_score is not None for u in unidades)
    assert all(0 <= u.overall_score <= 100 for u in unidades)

def test_extract_compliance_multi_layer():
    _, unidades = extract(_make_analysis(imports=["fastapi", "boto3"]), ACTIVO_ID)
    funciones = [u for u in unidades if u.tipo == "FUNCION"]
    assert funciones[0].compliance["has_multi_layer_coupling"] is True

def test_extract_archivo_sin_funciones_ni_clases_retorna_vacio():
    _, unidades = extract(_make_analysis(functions=[], classes=[]), ACTIVO_ID)
    assert unidades == []
