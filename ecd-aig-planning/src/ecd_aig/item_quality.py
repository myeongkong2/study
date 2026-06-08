from __future__ import annotations

import re
from .models import Project
from .rendering import table, status_mark

VAGUE_TERMS = ("자주", "항상", "가끔", "대체로", "많이", "심하게", "충분히")
DOUBLE_TERMS = ("그리고", "및", "또는", "동시에", "뿐만 아니라")
SENSITIVE_TERMS = ("성별", "나이", "장애", "종교", "정치", "인종", "출신")
NEGATIVE_PATTERNS = ("아니다", "않다", "못한다", "없다")
AUTOMATED_SCREENING_NOTICE = (
    "Rule-based item screening identifies review candidates only. "
    "It does not replace expert judgment or establish item validity."
)
EXPERT_REVIEW_CRITERIA = [
    "construct alignment and possible construct drift",
    "single-signal interpretation beyond surface wording",
    "appropriateness of clinical or stigmatizing language in context",
    "response-scale fit and interpretation for the intended population",
    "content relevance, clarity, and fairness in the target setting",
]


def audit_item(item: dict, strict: bool = False) -> dict:
    stem = item.get("stem", "")
    issues: list[str] = []
    if len(stem) < 12:
        issues.append("stem_too_short")
    if len(stem) > 90:
        issues.append("stem_too_long")
    if "?" in stem:
        issues.append("question_form")
    if any(term in stem for term in DOUBLE_TERMS):
        issues.append("double_barreled_connector")
    if any(term in stem for term in VAGUE_TERMS):
        issues.append("vague_frequency_or_intensity")
    if sum(1 for term in NEGATIVE_PATTERNS if term in stem) > 1:
        issues.append("multiple_negation")
    if any(term in stem for term in SENSITIVE_TERMS):
        issues.append("sensitive_term")
    variables = item.get("variables") or {}
    if strict and not variables.get("work_situation"):
        issues.append("missing_single_work_situation")
    if strict and not variables.get("negative_response"):
        issues.append("missing_single_negative_response")
    if strict and len(str(variables.get("work_situation", "")).split(",")) > 1:
        issues.append("multiple_situations")
    return {
        "item_id": item.get("id"),
        "ok": not issues,
        "issues": issues,
        "stem": stem,
        "screening_type": "automated_rule_based",
        "requires_expert_review": True,
    }


def audit_project(project: Project, strict: bool = False) -> dict:
    items = [audit_item(item, strict=strict) for item in project.items]
    return {
        "ok": all(item["ok"] for item in items),
        "items": items,
        "screening_type": "automated_rule_based",
        "automated_screening_notice": AUTOMATED_SCREENING_NOTICE,
        "expert_review_criteria": EXPERT_REVIEW_CRITERIA,
    }


def audit_markdown(report: dict) -> str:
    rows = [[item["item_id"], status_mark(item["ok"]), ", ".join(item["issues"]) or "-"] for item in report["items"]]
    return (
        "# Item Quality Screening\n\n"
        + report["automated_screening_notice"]
        + "\n\n## Automated Rule Results\n\n"
        + table(["Item", "Status", "Issues"], rows)
        + "\n\n## Expert Review Still Required\n"
        + "\n".join(f"- {criterion}" for criterion in report["expert_review_criteria"])
    )
