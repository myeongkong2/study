from __future__ import annotations

from .models import Project
from .validation import validate_project
from .item_quality import audit_project
from .blueprint import blueprint_report
from .review import review_status
from .ecd_report import ecd_fit_report
from .caf import caf_report
from .toulmin import toulmin_argument
from .pre_response import VALIDITY_BOUNDARY


def dossier(project: Project, item_id: str | None = None, response: str | None = None, strict: bool = True) -> dict:
    selected_item = item_id or (project.items[-1]["id"] if project.items else None)
    return {
        "project_id": project.id,
        "title": project.title,
        "validation": validate_project(project),
        "item_quality": audit_project(project, strict=strict),
        "blueprint": blueprint_report(project),
        "review": review_status(project),
        "ecd_fit": ecd_fit_report(project),
        "caf": caf_report(project),
        "toulmin": toulmin_argument(project, selected_item, response) if selected_item else None,
        "report_type": "pre_response_dossier",
        "boundary": VALIDITY_BOUNDARY,
    }


def dossier_markdown(report: dict) -> str:
    validation = "PASS" if report["validation"]["ok"] else "FAIL"
    quality = "PASS" if report["item_quality"]["ok"] else "FAIL"
    review = "PASS" if report["review"]["ok"] else "FAIL"
    return "\n".join(
        [
            f"# ECD-AIG Dossier: {report['title']}",
            f"- Structural validation: {validation}",
            f"- Item quality audit: {quality}",
            f"- Expert review workflow: {review}",
            f"- ECD fit: {report['ecd_fit']['interpretation']}",
            f"- Validity boundary: {report['boundary']}",
            "\n## Toulmin Snapshot",
            f"- Claim: {report['toulmin']['claim'] if report['toulmin'] else '-'}",
            f"- Qualifier: {report['toulmin']['qualifier'] if report['toulmin'] else '-'}",
        ]
    )
