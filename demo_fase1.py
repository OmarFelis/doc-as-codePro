"""
Script de demostración de la Fase 1.
Corre el pipeline completo contra los fixtures de microservicios
o contra cualquier ruta real del sistema de archivos.
Usa SQLite en memoria — sin necesitar Postgres ni AWS.

Uso:
    poetry run python demo_fase1.py
    poetry run python demo_fase1.py --fixture dominio_puro
    poetry run python demo_fase1.py --path C:/repos/mi-microservicio
    poetry run python demo_fase1.py --path ./src --name MiServicio
"""
import asyncio
import argparse
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import Base
from src.db import repository as repo
from src.core.analyzers import pipeline

FIXTURES_DIR = Path("tests/fixtures/microservicios")

FIXTURES = {
    "dominio_puro":          "dominio_puro.py",
    "multicapa":             "acoplamiento_multicapa.py",
    "infraestructura":       "infraestructura_pura.py",
    "alta_complejidad":      "alta_complejidad.py",
    "todos":                 None,  # usa el directorio completo
}


class QualityAuditORMDemo(Base):
    __tablename__ = "qa_demo"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), nullable=True)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    runtime_env = Column(String(50), nullable=True)
    language = Column(String(50), nullable=True)
    risk_level = Column(String(10), nullable=False, default="MEDIUM")
    overall_score = Column(Float, nullable=True)
    description = Column(JSON, nullable=False, default=dict)
    external_relations = Column(JSON, nullable=False, default=dict)
    metrics = Column(JSON, nullable=False, default=dict)
    compliance = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def _make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[QualityAuditORMDemo.__table__])
    original = repo.QualityAuditORM
    repo.QualityAuditORM = QualityAuditORMDemo
    session = sessionmaker(bind=engine)()
    return session, original


def _print_separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def _print_units(session, parent_id: str):
    children = repo.get_by_parent(session, parent_id)
    if not children:
        print("  (sin unidades logicas detectadas)")
        return

    risk_icon = {"LOW": "[LOW]", "MEDIUM": "[MED]", "HIGH": "[HIGH]"}
    layer_icon = {"dominio": "[DOM]", "adaptador": "[ADP]", "infraestructura": "[INF]"}

    for u in children:
        layer = u.metrics.get("architecture_layer", "?")
        icon = risk_icon.get(u.risk_level, "[?]")
        licon = layer_icon.get(layer, "[?]")
        score = f"{u.overall_score:.1f}" if u.overall_score else "N/A"
        coupling = " ** MULTICAPA **" if u.compliance.get("has_multi_layer_coupling") else ""
        print(f"  {icon} {licon}  {u.entity_name:<35} score={score:<6} risk={u.risk_level}{coupling}")


async def demo(fixture_name: str):
    session, original_orm = _make_session()

    try:
        if fixture_name == "todos":
            project_path = FIXTURES_DIR
            ms_name = "ACS-COMPLETO"
        else:
            filename = FIXTURES[fixture_name]
            # Crear directorio temporal con solo ese fixture
            import tempfile, shutil
            tmp = Path(tempfile.mkdtemp())
            shutil.copy(FIXTURES_DIR / filename, tmp / filename)
            project_path = tmp
            ms_name = fixture_name.upper().replace("_", "-")

        _print_separator(f"Pipeline: {ms_name}  ({project_path})")

        summary = await pipeline.run(project_path, ms_name, session)
        session.commit()

        # Quality Summary
        print(f"\nQUALITY SUMMARY")
        print(f"  Microservicio ID : {summary['microservice_id']}")
        print(f"  Overall Score    : {summary['overall_score']}")
        print(f"  Risk Level       : {summary['risk_level']}")
        print(f"  Unidades logicas : {summary['units_count']}")
        print(f"  Unidades HIGH    : {summary['high_risk_units']}")
        print(f"  Reglas negocio   : {summary['business_rules_count']} (requiere LLM)")

        # Detalle de unidades
        print(f"\nUNIDADES LOGICAS DETECTADAS")
        _print_units(session, summary["microservice_id"])

        # Registro en BD
        parent = repo.get_by_name(session, ms_name)
        print(f"\nPERSISTIDO EN BD")
        print(f"  entity_name  : {parent.entity_name}")
        print(f"  entity_type  : {parent.entity_type}")
        print(f"  language     : {parent.language}")
        print(f"  metrics      : {json.dumps(parent.metrics, indent=4)}")

    finally:
        session.close()
        repo.QualityAuditORM = original_orm
        if fixture_name != "todos" and 'tmp' in locals():
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


async def demo_path(path: str, name: str):
    """Corre el pipeline contra una ruta real del sistema de archivos."""
    project_path = Path(path).resolve()
    if not project_path.exists():
        print(f"[ERROR] Ruta no encontrada: {project_path}")
        return

    session, original_orm = _make_session()
    try:
        _print_separator(f"Pipeline: {name}  ({project_path})")
        summary = await pipeline.run(project_path, name, session)
        session.commit()

        print(f"\nQUALITY SUMMARY")
        print(f"  Microservicio ID : {summary['microservice_id']}")
        print(f"  Overall Score    : {summary['overall_score']}")
        print(f"  Risk Level       : {summary['risk_level']}")
        print(f"  Unidades logicas : {summary['units_count']}")
        print(f"  Unidades HIGH    : {summary['high_risk_units']}")
        print(f"  Reglas negocio   : {summary['business_rules_count']} (requiere LLM)")

        print(f"\nUNIDADES LOGICAS DETECTADAS")
        _print_units(session, summary["microservice_id"])

        parent = repo.get_by_name(session, name)
        print(f"\nPERSISTIDO EN BD")
        print(f"  entity_name  : {parent.entity_name}")
        print(f"  entity_type  : {parent.entity_type}")
        print(f"  language     : {parent.language}")
        print(f"  metrics      : {json.dumps(parent.metrics, indent=4)}")
    finally:
        session.close()
        repo.QualityAuditORM = original_orm


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo Fase 1 — Code-Agent")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--fixture",
        choices=list(FIXTURES.keys()),
        help="Fixture predefinido a analizar",
    )
    group.add_argument(
        "--path",
        help="Ruta real a analizar (directorio o archivo .py)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Nombre del microservicio (default: nombre del directorio)",
    )
    args = parser.parse_args()

    if args.path:
        ms_name = args.name or Path(args.path).resolve().name
        asyncio.run(demo_path(args.path, ms_name))
    else:
        asyncio.run(demo(args.fixture or "todos"))
