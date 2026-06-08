from __future__ import annotations

import re
from collections import Counter
from .models import Project, result

SENSITIVE_TERMS = ("성별", "나이", "장애", "종교", "정치", "임신", "출신", "인종")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


def validate_traceability(project: Project) -> dict:
    construct_ids = project.ids("constructs")
    ksa_ids = project.ids("ksas")
    claim_ids = project.ids("evidence_claims")
    task_model_ids = project.ids("task_models")
    template_ids = project.ids("parent_templates")
    ksa_by_id = {ksa.get("id"): ksa for ksa in project.ksas}
    claim_by_id = {claim.get("id"): claim for claim in project.evidence_claims}
    template_by_id = {template.get("id"): template for template in project.parent_templates}
    problems = []
    for ksa in project.ksas:
        if ksa.get("construct_id") not in construct_ids:
            problems.append(f"{ksa.get('id', '<missing KSA>')}: missing/unknown construct_id")
    for claim in project.evidence_claims:
        if claim.get("ksa_id") not in ksa_ids:
            problems.append(f"{claim.get('id', '<missing claim>')}: missing/unknown ksa_id")
    for template in project.parent_templates:
        template_id = template.get("id", "<missing template>")
        if template.get("construct_id") not in construct_ids:
            problems.append(f"{template_id}: missing/unknown construct_id")
        if template.get("ksa_id") not in ksa_ids:
            problems.append(f"{template_id}: missing/unknown ksa_id")
        if template.get("evidence_claim_id") not in claim_ids:
            problems.append(f"{template_id}: missing/unknown evidence_claim_id")
        if template.get("task_model_id") not in task_model_ids:
            problems.append(f"{template_id}: missing/unknown task_model_id")
        ksa = ksa_by_id.get(template.get("ksa_id"))
        claim = claim_by_id.get(template.get("evidence_claim_id"))
        if ksa and ksa.get("construct_id") != template.get("construct_id"):
            problems.append(f"{template_id}: construct_id does not match linked KSA")
        if claim and claim.get("ksa_id") != template.get("ksa_id"):
            problems.append(f"{template_id}: evidence_claim_id does not match linked KSA")
    for item in project.items:
        item_id = item.get("id", "<missing>")
        if item.get("construct_id") not in construct_ids:
            problems.append(f"{item_id}: missing/unknown construct_id")
        if item.get("ksa_id") not in ksa_ids:
            problems.append(f"{item_id}: missing/unknown ksa_id")
        if item.get("evidence_claim_id") not in claim_ids:
            problems.append(f"{item_id}: missing/unknown evidence_claim_id")
        if item.get("task_model_id") not in task_model_ids:
            problems.append(f"{item_id}: missing/unknown task_model_id")
        if item.get("parent_template_id") not in template_ids:
            problems.append(f"{item_id}: missing/unknown parent_template_id")
        if not isinstance(item.get("variables"), dict):
            problems.append(f"{item_id}: variables must be an object")
        ksa = ksa_by_id.get(item.get("ksa_id"))
        claim = claim_by_id.get(item.get("evidence_claim_id"))
        template = template_by_id.get(item.get("parent_template_id"))
        if ksa and ksa.get("construct_id") != item.get("construct_id"):
            problems.append(f"{item_id}: construct_id does not match linked KSA")
        if claim and claim.get("ksa_id") != item.get("ksa_id"):
            problems.append(f"{item_id}: evidence_claim_id does not match linked KSA")
        if template:
            for field in ("construct_id", "ksa_id", "evidence_claim_id", "task_model_id"):
                if template.get(field) != item.get(field):
                    problems.append(f"{item_id}: {field} does not match parent template")
    return result(not problems, "traceability", "ECD lineage links are connected" if not problems else "Traceability problems found", problems=problems)


def validate_scoring_readiness(project: Project) -> dict:
    anchors = project.response_scale.get("anchors", [])
    anchor_scores = {a.get("score") for a in anchors}
    problems = []
    if len(anchors) < 2:
        problems.append("response_scale.anchors must contain at least two anchors")
    for item in project.items:
        item_id = item.get("id", "<missing>")
        scoring = item.get("scoring") or {}
        if "direction" not in scoring:
            problems.append(f"{item_id}: scoring.direction is missing")
        valid_scores = set(scoring.get("valid_scores") or [])
        if valid_scores and not valid_scores.issubset(anchor_scores):
            problems.append(f"{item_id}: valid_scores not compatible with response_scale")
    return result(not problems, "scoring_readiness", "Scoring metadata is ready" if not problems else "Scoring metadata problems found", problems=problems)


def validate_redundancy(project: Project) -> dict:
    normalized = [normalize_text(item.get("stem", "")) for item in project.items]
    counts = Counter(x for x in normalized if x)
    duplicates = [stem for stem, count in counts.items() if count > 1]
    return result(not duplicates, "redundancy", "No deterministic duplicate stems found" if not duplicates else "Duplicate stems found", duplicates=duplicates)


def validate_sensitivity(project: Project) -> dict:
    hits = []
    for item in project.items:
        stem = item.get("stem", "")
        terms = [term for term in SENSITIVE_TERMS if term in stem]
        if terms:
            hits.append({"item_id": item.get("id"), "terms": terms})
    return result(not hits, "sensitivity", "No watch-list sensitive terms found" if not hits else "Sensitive watch-list hits found", hits=hits)


def validate_project(project: Project) -> dict:
    gates = [
        validate_traceability(project),
        validate_scoring_readiness(project),
        validate_redundancy(project),
        validate_sensitivity(project),
    ]
    return {"ok": all(gate["ok"] for gate in gates), "gates": gates}
