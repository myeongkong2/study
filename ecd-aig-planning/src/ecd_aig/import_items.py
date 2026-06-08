from __future__ import annotations

import json
from pathlib import Path
from .models import Project


def import_candidate_items(path: str | Path) -> Project:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = []
    for index, item in enumerate(data.get("items", []), start=1):
        items.append(
            {
                "id": item.get("id") or f"IMP-{index:03d}",
                # Imported candidates keep missing lineage visibly missing.
                # Measurement meaning must be declared by a human-authored design model.
                "construct_id": item.get("construct_id"),
                "ksa_id": item.get("ksa_id"),
                "evidence_claim_id": item.get("evidence_claim_id"),
                "task_model_id": item.get("task_model_id", "task_self_report_likert"),
                "parent_template_id": item.get("parent_template_id", "tpl_imported_candidate"),
                "variables": item.get("variables") or {},
                "stem": item["stem"],
                "rationale": item.get("rationale", ""),
                "scoring": item.get("scoring") or {"direction": "positive", "valid_scores": [1, 2, 3, 4, 5]},
                "status": "imported_candidate",
            }
        )
    return Project.from_dict(
        {
            "id": data.get("id", "imported_project"),
            "title": data.get("title", "Imported Candidate Items"),
            "constructs": data.get("constructs") or [],
            "ksas": data.get("ksas") or [],
            "evidence_claims": data.get("evidence_claims") or [],
            "task_models": data.get("task_models") or [{"id": "task_self_report_likert", "name": "5-point Likert self-report"}],
            "parent_templates": data.get("parent_templates")
            or [
                {
                    "id": "tpl_imported_candidate",
                    "stem_template": "{stem}",
                    "variables": {},
                    "source": "import_container_only",
                }
            ],
            "response_scale": data.get("response_scale") or default_response_scale(),
            "items": items,
            "reviews": [],
        }
    )


def default_response_scale() -> dict:
    return {
        "type": "5-point Likert",
        "anchors": [
            {"score": 1, "label": "Strongly disagree"},
            {"score": 2, "label": "Disagree"},
            {"score": 3, "label": "Neither agree nor disagree"},
            {"score": 4, "label": "Agree"},
            {"score": 5, "label": "Strongly agree"},
        ],
    }
