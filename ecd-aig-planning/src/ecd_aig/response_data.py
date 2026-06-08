from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean
from .models import Project
from .scoring import score_response


def load_responses(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_responses(project: Project, path: str | Path) -> dict:
    rows = load_responses(path)
    item_ids = [item["id"] for item in project.items]
    problems = []
    scored_rows = []
    for row_index, row in enumerate(rows, start=2):
        scored = {"respondent_id": row.get("respondent_id", str(row_index))}
        for item_id in item_ids:
            value = row.get(item_id, "")
            if value == "":
                scored[item_id] = None
                continue
            try:
                scored[item_id] = score_response(project, item_id, value)["score"]
            except Exception as exc:
                problems.append(f"row {row_index} {item_id}: {exc}")
        scored_rows.append(scored)
    totals = [sum(v for k, v in row.items() if k != "respondent_id" and isinstance(v, int)) for row in scored_rows]
    return {
        "ok": not problems,
        "respondents": len(rows),
        "items": len(item_ids),
        "problems": problems,
        "mean_total": mean(totals) if totals else None,
        "scored_rows": scored_rows,
    }

