from __future__ import annotations

from itertools import product
from .models import Project
from .validation import validate_project


def generate_items(project: Project, template_id: str, count: int) -> list[dict]:
    template = project.template_by_id(template_id)
    variables = template.get("variables") or {}
    keys = list(variables)
    combinations = list(product(*[variables[key] for key in keys]))
    start = len(project.items) + 1
    generated = []
    for offset, combo in enumerate(combinations[:count], start=0):
        values = dict(zip(keys, combo))
        stem = template["stem_template"].format(**values)
        generated.append(
            {
                "id": f"GEN-{start + offset:03d}",
                "construct_id": template.get("construct_id"),
                "ksa_id": template.get("ksa_id"),
                "evidence_claim_id": template.get("evidence_claim_id"),
                "task_model_id": template.get("task_model_id"),
                "parent_template_id": template_id,
                "variables": values,
                "stem": stem,
                "rationale": template.get("rationale", ""),
                "scoring": {"direction": "positive", "valid_scores": [1, 2, 3, 4, 5]},
                "status": "generated",
            }
        )
    return generated


def generate_with_validation(project: Project, template_id: str, count: int) -> dict:
    items = generate_items(project, template_id, count)
    probe = Project.from_dict(project.to_dict())
    probe.items = project.items + items
    validation = validate_project(probe)
    return {"ok": validation["ok"], "items": items, "validation": validation}

