"""
Prueba manual del pipeline Fase 1 — sin BD.
Modos:
    # Un repo (detallado)
    poetry run python run_test.py <ruta>

    # Comparar múltiples repos (resumen)
    poetry run python run_test.py --compare <ruta1> <ruta2> ...
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.analyzers.project_analyzer import ProjectAnalyzerService
from src.core.analyzers import logical_unit_extractor
from src.models.domain import RiskLevel


def _analyze(project_path: Path) -> dict:
    """Analiza un repo y retorna métricas + unidades."""
    activo_id = str(uuid.uuid4())
    project = ProjectAnalyzerService().analyze_project(project_path, project_path.name)
    all_unidades = []
    for fa in project.files:
        _, unidades = logical_unit_extractor.extract(fa, activo_id)
        all_unidades.extend(unidades)

    funciones = [u for u in all_unidades if u.tipo == "FUNCION"]
    clases = [u for u in all_unidades if u.tipo == "CLASE"]
    scores = [u.overall_score for u in funciones if u.overall_score is not None]
    high = [u for u in funciones if u.risk_level == RiskLevel.HIGH]
    medium = [u for u in funciones if u.risk_level == RiskLevel.MEDIUM]

    return {
        "path": project_path,
        "archivos": project.total_files,
        "loc": project.total_lines,
        "clases": len(clases),
        "funciones": len(funciones),
        "score_avg": round(sum(scores) / len(scores), 1) if scores else 0,
        "score_min": round(min(scores), 1) if scores else 0,
        "high": len(high),
        "medium": len(medium),
        "files": project.files,
        "unidades": all_unidades,
        "activo_id": activo_id,
    }


def _print_detail(project_path: Path):
    activo_id = str(uuid.uuid4())
    print(f"\n{'='*60}")
    print(f"  Pipeline: {project_path.name}  ({project_path.resolve()})")
    print(f"{'='*60}")

    project = ProjectAnalyzerService().analyze_project(project_path, project_path.name)
    total_archivos = total_clases = total_funciones = 0

    for fa in project.files:
        archivo, unidades = logical_unit_extractor.extract(fa, activo_id)
        clases = [u for u in unidades if u.tipo == "CLASE"]
        funciones = [u for u in unidades if u.tipo == "FUNCION"]
        total_archivos += 1
        total_clases += len(clases)
        total_funciones += len(funciones)

        print(f"[ARCHIVO] {archivo.nombre}  capa={archivo.capa}  loc={archivo.lineas_codigo}")
        for clase in clases:
            print(f"  [CLASE]   {clase.nombre}  risk={clase.risk_level}  score={clase.overall_score}")
            for fn in [u for u in funciones if u.parent_id == clase.id]:
                print(f"    [FUNC]  {fn.nombre}  risk={fn.risk_level}  score={fn.overall_score}")
        for fn in [u for u in funciones if u.parent_id is None]:
            print(f"  [FUNC]    {fn.nombre}  risk={fn.risk_level}  score={fn.overall_score}")
        if unidades:
            print()

    print(f"{'='*60}")
    print(f"  archivos_total  : {total_archivos}")
    print(f"  clases_total    : {total_clases}")
    print(f"  funciones_total : {total_funciones}")
    print(f"{'='*60}\n")


def _print_compare(paths: list[Path]):
    results = []
    for p in paths:
        print(f"Analizando {p.name}...", flush=True)
        results.append(_analyze(p))

    # Header
    col = 22
    print(f"\n{'='*80}")
    print(f"  COMPARATIVA DE REPOS")
    print(f"{'='*80}")
    header = f"{'Repo':<{col}} {'Arch':>5} {'LOC':>6} {'Cls':>5} {'Func':>5} {'Avg':>6} {'Min':>6} {'HIGH':>5} {'MED':>5}"
    print(header)
    print("-" * 80)

    for r in sorted(results, key=lambda x: x["score_avg"]):
        risk_flag = " ⚠" if r["high"] > 0 else ""
        print(
            f"  {r['path'].name:<{col}} "
            f"{r['archivos']:>5} "
            f"{r['loc']:>6} "
            f"{r['clases']:>5} "
            f"{r['funciones']:>5} "
            f"{r['score_avg']:>6} "
            f"{r['score_min']:>6} "
            f"{r['high']:>5} "
            f"{r['medium']:>5}"
            f"{risk_flag}"
        )

    print(f"{'='*80}")

    # Top 5 funciones con score más bajo (candidatas a refactor)
    all_funcs = []
    for r in results:
        for u in r["unidades"]:
            if u.tipo == "FUNCION" and u.overall_score is not None:
                all_funcs.append((r["path"].name, u.nombre, u.capa, u.risk_level, u.overall_score))

    worst = sorted(all_funcs, key=lambda x: x[4])[:10]
    if worst:
        print(f"\n  TOP 10 funciones con score más bajo (candidatas a refactor):")
        print(f"  {'Repo':<20} {'Función':<35} {'Capa':<15} {'Risk':<8} {'Score'}")
        print("  " + "-" * 75)
        for repo, nombre, capa, risk, score in worst:
            print(f"  {repo:<20} {nombre:<35} {capa:<15} {risk:<8} {score}")
    print()


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: poetry run python run_test.py <ruta>")
        print("     poetry run python run_test.py --compare <ruta1> <ruta2> ...")
        sys.exit(1)

    if args[0] == "--compare":
        paths = [Path(a) for a in args[1:]]
        if len(paths) < 2:
            print("--compare requiere al menos 2 rutas")
            sys.exit(1)
        _print_compare(paths)
    else:
        _print_detail(Path(args[0]))


if __name__ == "__main__":
    main()
