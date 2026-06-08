from __future__ import annotations

from .models import Project


def ecd_fit_report(project: Project) -> dict:
    complete_items = sum(
        1
        for item in project.items
        if item.get("construct_id") and item.get("ksa_id") and item.get("evidence_claim_id") and item.get("parent_template_id")
    )
    return {
        "ok": complete_items == len(project.items),
        "items_with_complete_lineage": complete_items,
        "total_items": len(project.items),
        "interpretation": "ECD links are complete enough for pre-response design review." if complete_items == len(project.items) else "Some items lack complete ECD linkage.",
        "validity_boundary": "Complete ECD linkage is necessary for design review, but it is not empirical validity evidence.",
    }
