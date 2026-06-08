from __future__ import annotations

from .models import Project


def caf_report(project: Project) -> dict:
    return {
        "student_model": project.constructs,
        "evidence_model": project.evidence_claims,
        "task_model": project.task_models,
        "task_evidence_composite": [
            {
                "item_id": item.get("id"),
                "construct_id": item.get("construct_id"),
                "ksa_id": item.get("ksa_id"),
                "evidence_claim_id": item.get("evidence_claim_id"),
                "parent_template_id": item.get("parent_template_id"),
            }
            for item in project.items
        ],
        "four_process_architecture": {
            "activity_selection": "Select parent template and task-variable combination.",
            "presentation": "Present Korean self-report Likert item stem and response scale.",
            "response_processing": "Map selected anchor to ordinal score with reverse scoring if needed.",
            "summary_scoring": "Aggregate only after pilot validation and approved scoring model.",
        },
        "validity_boundary": "Design-stage evidence only; empirical reliability, factor structure, IRT, and DIF require pilot data.",
    }


def caf_markdown(report: dict) -> str:
    lines = ["# CAF Design Map", "## Student Model"]
    lines.extend(f"- {x.get('id')}: {x.get('name')}" for x in report["student_model"])
    lines.append("\n## Evidence Model")
    lines.extend(f"- {x.get('id')}: {x.get('claim')}" for x in report["evidence_model"])
    lines.append("\n## Task Model")
    lines.extend(f"- {x.get('id')}: {x.get('name')}" for x in report["task_model"])
    lines.append("\n## Four-Process Architecture")
    lines.extend(f"- {key}: {value}" for key, value in report["four_process_architecture"].items())
    lines.append("\n## Validity Boundary\n" + report["validity_boundary"])
    return "\n".join(lines)

