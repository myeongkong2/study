from __future__ import annotations

from .models import Project
from .validation import validate_project
from .rendering import table


VALID_DECISIONS = {"approve", "reject", "revise"}


def review_status(project: Project) -> dict:
    review_by_item = {review.get("item_id"): review for review in project.reviews}
    validation = validate_project(project)
    failing = set()
    for gate in validation["gates"]:
        if not gate["ok"]:
            for problem in gate.get("problems", []):
                failing.add(problem.split(":")[0])
    rows = []
    problems = []
    for item in project.items:
        item_id = item.get("id")
        review = review_by_item.get(item_id, {})
        decision = review.get("decision")
        if decision not in VALID_DECISIONS:
            problems.append(f"{item_id}: missing expert decision")
        if item_id in failing and decision == "approve":
            problems.append(f"{item_id}: approved despite validation failure")
        rows.append({"item_id": item_id, "decision": decision or "missing", "reviewer": review.get("reviewer", "-")})
    return {"ok": not problems, "items": rows, "problems": problems}


def review_markdown(report: dict) -> str:
    rows = [[x["item_id"], x["decision"], x["reviewer"]] for x in report["items"]]
    text = "# Expert Review Status\n\n" + table(["Item", "Decision", "Reviewer"], rows)
    if report["problems"]:
        text += "\n\n## Problems\n" + "\n".join(f"- {problem}" for problem in report["problems"])
    return text

