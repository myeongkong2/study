from __future__ import annotations

from itertools import product
from .models import Project


def simulation_summary(project: Project) -> dict:
    template_rows = []
    total_possible = 0
    for template in project.parent_templates:
        variables = template.get("variables") or {}
        counts = [len(values) for values in variables.values()]
        possible = 1
        for count in counts:
            possible *= count
        total_possible += possible
        existing = sum(1 for item in project.items if item.get("parent_template_id") == template.get("id"))
        template_rows.append(
            {
                "template_id": template.get("id"),
                "possible_combinations": possible,
                "existing_items": existing,
                "coverage_ratio": round(existing / possible, 3) if possible else None,
            }
        )
    return {"ok": True, "templates": template_rows, "total_possible_combinations": total_possible, "current_items": len(project.items)}

