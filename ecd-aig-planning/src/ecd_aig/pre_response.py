from __future__ import annotations

from .blueprint import blueprint_report
from .caf import caf_report
from .ecd_report import ecd_fit_report
from .item_quality import audit_project
from .models import Project
from .rendering import table
from .review import review_status
from .validation import validate_project


VALIDITY_BOUNDARY = (
    "Pre-response screening supports design traceability and risk detection only. "
    "It does not establish empirical reliability, validity, calibration, or fairness."
)

SUPPORTED_CLAIMS = [
    "ECD lineage can be traced from each item to its declared construct, KSA, evidence claim, task model, and parent template.",
    "Declared scoring metadata, deterministic duplicates, and watch-list terms can be screened before administration.",
    "Candidate items can be prioritized for revision and expert review before pilot administration.",
]

REQUIRES_RESPONSE_DATA = [
    "reliability estimates such as Cronbach alpha",
    "item-total correlations and empirical item behavior",
    "factor structure and dimensionality",
    "IRT calibration and item parameters",
    "DIF and empirical fairness analysis",
    "operational validity claims",
]


def pre_response_readiness(project: Project, strict: bool = True) -> dict:
    structural = validate_project(project)
    quality = audit_project(project, strict=strict)
    review = review_status(project)
    blockers = []
    for gate in structural["gates"]:
        if not gate["ok"]:
            blockers.append(
                {
                    "source": "structural_gate",
                    "code": gate["code"],
                    "details": gate.get("problems") or gate.get("hits") or gate.get("duplicates") or [],
                }
            )
    for item in quality["items"]:
        if not item["ok"]:
            blockers.append({"source": "item_quality_gate", "code": item["item_id"], "details": item["issues"]})

    if blockers:
        status = "revision_required"
    elif not review["ok"]:
        status = "ready_for_expert_review"
    else:
        status = "ready_for_pilot_administration"

    return {
        "report_type": "pre_response_readiness",
        "project_id": project.id,
        "title": project.title,
        "status": status,
        "structural_screening": structural,
        "item_quality_screening": quality,
        "expert_judgment_required": quality["expert_review_criteria"],
        "expert_review": review,
        "blueprint": blueprint_report(project),
        "ecd_fit": ecd_fit_report(project),
        "caf": caf_report(project),
        "blockers": blockers,
        "supported_claims": SUPPORTED_CLAIMS,
        "requires_response_data": REQUIRES_RESPONSE_DATA,
        "validity_boundary": VALIDITY_BOUNDARY,
    }


def pre_response_markdown(report: dict) -> str:
    rows = [
        ["Structural screening", "PASS" if report["structural_screening"]["ok"] else "FAIL"],
        ["Item-quality screening", "PASS" if report["item_quality_screening"]["ok"] else "FAIL"],
        ["Expert review workflow", "PASS" if report["expert_review"]["ok"] else "INCOMPLETE"],
    ]
    lines = [
        f"# Pre-response Readiness: {report['title']}",
        f"- Status: {report['status']}",
        "",
        table(["Area", "Result"], rows),
        "",
        "## Validity Boundary",
        report["validity_boundary"],
        "",
        "## Supported Claims",
        *[f"- {claim}" for claim in report["supported_claims"]],
        "",
        "## Requires Response Data",
        *[f"- {claim}" for claim in report["requires_response_data"]],
    ]
    if report["blockers"]:
        lines.extend(["", "## Revision Blockers"])
        lines.extend(f"- {blocker['source']} / {blocker['code']}: {blocker['details']}" for blocker in report["blockers"])
    return "\n".join(lines)
