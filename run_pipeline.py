"""
Pipeline completo Fase 1 + Fase 2.
Uso:
    poetry run python run_pipeline.py <ruta_proyecto> [nombre] [--enrich] [--dry-run]

  --dry-run  : SQLite en memoria (sin PostgreSQL, genera activo_id automático)
  --enrich   : activa enriquecimiento Strands + Bedrock

Ejemplos:
    poetry run python run_pipeline.py C:/mvpRBAMOTORBACK --dry-run
    poetry run python run_pipeline.py C:/mvpRBAMOTORBACK --dry-run --enrich
    poetry run python run_pipeline.py C:/mvpRBAMOTORBACK 550e8400-e29b-41d4-a716-446655440000 --enrich
"""
import sys
import uuid
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.analyzers.pipeline import run
from src.utils.logging import setup_logging, get_logger

setup_logging(debug=False)
logger = get_logger(__name__)

DRY_RUN_UUID = str(uuid.uuid4())


def _dry_run_session():
    """Sesión SQLite en memoria compatible con los modelos ORM (sin JSONB)."""
    from datetime import datetime, timezone
    from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer, JSON, Text
    from sqlalchemy.orm import sessionmaker, DeclarativeBase
    from sqlalchemy.pool import StaticPool
    from src.db import repository as repo

    class _Base(DeclarativeBase):
        pass

    class _Archivo(_Base):
        __tablename__ = "archivos_fuente_dry"
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        activo_id = Column(String(36)); aplicacion_id = Column(String(255), nullable=True)
        nombre = Column(String(255)); ruta_archivo = Column(Text)
        proposito = Column(Text, nullable=True); capa = Column(String(50), nullable=True)
        lenguaje = Column(String(50), nullable=True)
        total_funciones = Column(Integer, default=0); total_clases = Column(Integer, default=0)
        endpoints = Column(JSON, default=list); operaciones_bd = Column(JSON, default=list)
        llamadas_externas = Column(JSON, default=list)
        complejidad_ciclomatica = Column(Integer, default=0); lineas_codigo = Column(Integer, default=0)
        resumen = Column(Text, nullable=True); metadata_ = Column("metadata", JSON, default=dict)
        build_number = Column(String(100), nullable=True); commit_hash = Column(String(40), nullable=True)
        escaneado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))
        activo = Column(Boolean, default=True)

    class _Unidad(_Base):
        __tablename__ = "unidades_logicas_dry"
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        archivo_id = Column(String(36), nullable=True); parent_id = Column(String(36), nullable=True)
        activo_id = Column(String(36)); nombre = Column(String(255)); tipo = Column(String(20))
        capa = Column(String(50), nullable=True); proposito = Column(Text, nullable=True)
        complejidad = Column(Integer, default=0); lineas_codigo = Column(Integer, default=0)
        accede_bd = Column(Boolean, default=False); llamadas_externas = Column(JSON, default=list)
        docstring = Column(Boolean, default=False); resumen = Column(Text, nullable=True)
        metadata_ = Column("metadata", JSON, default=dict)
        risk_level = Column(String(10), default="MEDIUM"); overall_score = Column(Float, nullable=True)
        compliance = Column(JSON, default=dict); activo = Column(Boolean, default=True)

    class _Escaneo(_Base):
        __tablename__ = "escaneos_dry"
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        activo_id = Column(String(36)); aplicacion_id = Column(String(255), nullable=True)
        build_number = Column(String(100), nullable=True); commit_hash = Column(String(40), nullable=True)
        escaneado_en = Column(DateTime, default=lambda: datetime.now(timezone.utc))
        generado_por = Column(String(100), default="code-agent-v1")
        score_general = Column(Float, nullable=True); nivel_riesgo = Column(String(10), nullable=True)
        archivos_total = Column(Integer, default=0); funciones_total = Column(Integer, default=0)
        clases_total = Column(Integer, default=0); dominios_negocio = Column(JSON, default=list)
        metricas = Column(JSON, default=dict); arquitectura = Column(JSON, default=dict)
        seguridad = Column(JSON, default=dict); rendimiento = Column(JSON, default=dict)
        negocio = Column(JSON, default=dict); cumplimiento = Column(JSON, default=dict)

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    _Base.metadata.create_all(engine)
    repo.ArchivoFuenteORM, repo.UnidadLogicaORM, repo.EscaneoORM = _Archivo, _Unidad, _Escaneo
    return sessionmaker(bind=engine)()


async def main():
    if len(sys.argv) < 2:
        print("Uso: poetry run python run_pipeline.py <ruta_proyecto> [nombre] [--enrich] [--dry-run]")
        sys.exit(1)

    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    enrich  = "--enrich"  in args
    verbose = "--show-enrichment" in args
    max_files = None
    aplicacion_id = None
    for a in args:
        if a.startswith("--max-files="):
            max_files = int(a.split("=")[1])
        if a.startswith("--aplicacion-id="):
            aplicacion_id = a.split("=")[1]
    positional = [a for a in args if not a.startswith("--")]

    project_path = Path(positional[0])
    if dry_run:
        activo_id = DRY_RUN_UUID
        name = positional[1] if len(positional) > 1 else project_path.name
    else:
        if len(positional) < 2:
            print("Sin --dry-run debes pasar <activo_id>")
            sys.exit(1)
        activo_id = positional[1]
        name = positional[2] if len(positional) > 2 else project_path.name

    print(f"\n{'='*60}")
    print(f"  Proyecto  : {project_path.resolve()}")
    print(f"  Activo ID : {activo_id}{'  (generado)' if dry_run else ''}")
    print(f"  Nombre    : {name}")
    print(f"  Modo      : {'🧪 dry-run (SQLite)' if dry_run else '🗄️  PostgreSQL'}")
    print(f"  Enrich    : {'✅ Bedrock (boto3)' if enrich else '❌ solo parseo'}")
    print(f"  Aplicacion: {aplicacion_id or 'N/A (dry-run)'}")
    if enrich and max_files:
        print(f"  Max-files : {max_files} (solo los más complejos)")
    if verbose:
        print(f"  Verbose   : ✅ imprimiendo JSON de enriquecimiento")
    print(f"{'='*60}\n")

    if dry_run:
        session = _dry_run_session()
    else:
        from src.db.session import init_db, get_session
        print("Inicializando BD...")
        try:
            init_db()
            print("  ✅ BD inicializada\n")
        except Exception as e:
            print(f"  ❌ Error init_db: {e}")
            sys.exit(1)
        session = get_session()
    try:
        agent = None
        if enrich:
            print("Cargando cliente Bedrock...")
            from src.core.enricher.llm_enricher import build_llm_client
            agent = build_llm_client()
            print(f"  {'✅ Cliente listo' if agent else '❌ Sin credenciales — continuando sin LLM'}\n")

        result = await run(
            project_path=project_path,
            activo_id=activo_id,
            microservice_name=name,
            session=session,
            aplicacion_id=aplicacion_id,
            llm_client=agent,
            max_files=max_files,
            verbose=verbose,
        )
        print(f"\n{'='*60}")
        print(f"  escaneo_id      : {result['escaneo_id']}")
        print(f"  score_general   : {result['score_general']}")
        print(f"  nivel_riesgo    : {result['nivel_riesgo']}")
        print(f"  archivos_total  : {result['archivos_total']}")
        print(f"  clases_total    : {result['clases_total']}")
        print(f"  funciones_total : {result['funciones_total']}")
        print(f"  enriquecido     : {result['enriquecido']}")
        print(f"{'='*60}\n")
    except Exception as e:
        logger.error("pipeline_failed", error=str(e), exc_info=True)
        print(f"\n❌ Pipeline falló: {e}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
