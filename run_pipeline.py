"""
Pipeline completo Fase 1 con persistencia PostgreSQL.
Uso:
    poetry run python run_pipeline.py <ruta_proyecto> <activo_id> [microservice_name]

Ejemplo:
    poetry run python run_pipeline.py C:/mvpRBAMOTORBACK 550e8400-e29b-41d4-a716-446655440000
    poetry run python run_pipeline.py C:/mvpRBAMOTORBACK 550e8400-e29b-41d4-a716-446655440000 mvpRBAMOTORBACK
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db.session import init_db, get_session
from src.core.analyzers.pipeline import run
from src.utils.logging import setup_logging, get_logger

setup_logging(debug=False)
logger = get_logger(__name__)


async def main():
    if len(sys.argv) < 3:
        print("Uso: poetry run python run_pipeline.py <ruta_proyecto> <activo_id> [nombre]")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    activo_id = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else project_path.name

    print(f"\n{'='*60}")
    print(f"  Proyecto  : {project_path.resolve()}")
    print(f"  Activo ID : {activo_id}")
    print(f"  Nombre    : {name}")
    print(f"{'='*60}\n")

    print("Inicializando BD (schemas code + quality)...")
    try:
        init_db()
        print("  ✅ BD inicializada\n")
    except Exception as e:
        print(f"  ❌ Error init_db: {e}")
        sys.exit(1)

    session = get_session()
    try:
        result = await run(
            project_path=project_path,
            activo_id=activo_id,
            microservice_name=name,
            session=session,
        )
        print(f"\n{'='*60}")
        print(f"  escaneo_id      : {result['escaneo_id']}")
        print(f"  score_general   : {result['score_general']}")
        print(f"  nivel_riesgo    : {result['nivel_riesgo']}")
        print(f"  archivos_total  : {result['archivos_total']}")
        print(f"  clases_total    : {result['clases_total']}")
        print(f"  funciones_total : {result['funciones_total']}")
        print(f"{'='*60}\n")
    except Exception as e:
        logger.error("pipeline_failed", error=str(e), exc_info=True)
        print(f"\n❌ Pipeline falló: {e}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
