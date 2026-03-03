"""Compara snapshots de unidades lógicas entre dos escaneos."""
from typing import List, Dict, Any
from src.models.domain import UnidadLogica


def compare(base: List[UnidadLogica], target: List[UnidadLogica]) -> Dict[str, Any]:
    base_map = {u.nombre: u for u in base}
    target_map = {u.nombre: u for u in target}

    base_names = set(base_map)
    target_names = set(target_map)

    added = list(target_names - base_names)
    removed = list(base_names - target_names)

    changed = []
    for name in base_names & target_names:
        b, t = base_map[name], target_map[name]
        diffs = {}
        if b.risk_level != t.risk_level:
            diffs["risk_level"] = {"base": b.risk_level, "target": t.risk_level}
        if b.overall_score != t.overall_score:
            diffs["overall_score"] = {"base": b.overall_score, "target": t.overall_score}
        if diffs:
            changed.append({"nombre": name, "changes": diffs})

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
            "total_base": len(base),
            "total_target": len(target),
        },
    }
