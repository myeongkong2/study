from __future__ import annotations

from math import sqrt
from statistics import mean
from .models import Project
from .response_data import validate_responses
from .rendering import table

MISSING_RATE_WARNING = 0.05
ALPHA_COMPLETE_CASE_WARNING = 0.8


def variance(values: list[float]) -> float:
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return sum((v - m) ** 2 for v in values) / (len(values) - 1)


def corr(xs: list[float], ys: list[float]) -> float | None:
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    xvals, yvals = zip(*pairs)
    vx = variance(list(xvals))
    vy = variance(list(yvals))
    if vx == 0 or vy == 0:
        return None
    mx, my = mean(xvals), mean(yvals)
    cov = sum((x - mx) * (y - my) for x, y in pairs) / (len(pairs) - 1)
    value = cov / sqrt(vx * vy)
    # Floating-point rounding can produce values such as 1.0000000000000002.
    return max(-1.0, min(1.0, value))


def psychometrics_report(project: Project, response_csv: str) -> dict:
    validated = validate_responses(project, response_csv)
    rows = validated["scored_rows"]
    item_ids = [item["id"] for item in project.items]
    item_stats = []
    totals = []
    for row in rows:
        values = [row.get(item_id) for item_id in item_ids]
        totals.append(sum(v for v in values if isinstance(v, int)))
    for item_id in item_ids:
        values = [row.get(item_id) for row in rows]
        numeric = [v for v in values if isinstance(v, int)]
        paired_values = []
        paired_rest_totals = []
        for total, row in zip(totals, rows):
            item_value = row.get(item_id)
            if isinstance(item_value, int):
                paired_values.append(item_value)
                paired_rest_totals.append(total - item_value)
        corrected_corr = corr(paired_values, paired_rest_totals)
        item_stats.append(
            {
                "item_id": item_id,
                "mean": round(mean(numeric), 3) if numeric else None,
                "sd": round(sqrt(variance(numeric)), 3) if len(numeric) > 1 else None,
                "missing": sum(1 for v in values if v is None),
                "corrected_item_total_corr": None if corrected_corr is None else round(corrected_corr, 3),
            }
        )
    complete_rows = [row for row in rows if all(isinstance(row.get(item_id), int) for item_id in item_ids)]
    complete_totals = [sum(row[item_id] for item_id in item_ids) for row in complete_rows]
    item_variances = [variance([row[item_id] for row in complete_rows]) for item_id in item_ids]
    k = len(item_ids)
    total_var = variance(complete_totals)
    alpha = None
    if k > 1 and len(complete_rows) > 1 and total_var > 0:
        alpha = (k / (k - 1)) * (1 - sum(item_variances) / total_var)
        alpha = min(1.0, alpha)
    respondent_count = len(rows)
    cell_count = respondent_count * len(item_ids)
    missing_cells = sum(item["missing"] for item in item_stats)
    missing_rate = missing_cells / cell_count if cell_count else 0.0
    complete_case_rate = len(complete_rows) / respondent_count if respondent_count else 0.0
    warnings = []
    if missing_rate > MISSING_RATE_WARNING:
        warnings.append(f"overall missing response rate exceeds {MISSING_RATE_WARNING:.0%}")
    if complete_case_rate < ALPHA_COMPLETE_CASE_WARNING:
        warnings.append(f"Cronbach alpha complete-case rate is below {ALPHA_COMPLETE_CASE_WARNING:.0%}")
    if alpha is None:
        warnings.append("Cronbach alpha could not be estimated from complete cases")
    return {
        "ok": validated["ok"],
        "cronbach_alpha": round(alpha, 3) if alpha is not None else None,
        "alpha_respondents": len(complete_rows),
        "missing_policy": {
            "item_statistics": "available responses per item",
            "corrected_item_total_corr": "pairwise complete responses for the target item and rest total",
            "cronbach_alpha": "complete cases across all project items",
        },
        "missing_summary": {
            "missing_cells": missing_cells,
            "total_response_cells": cell_count,
            "missing_rate": round(missing_rate, 3),
            "complete_case_rate": round(complete_case_rate, 3),
        },
        "warnings": warnings,
        "items": item_stats,
        "response_validation": validated,
    }


def psychometrics_markdown(report: dict) -> str:
    rows = [[x["item_id"], x["mean"], x["sd"], x["missing"], x["corrected_item_total_corr"]] for x in report["items"]]
    return (
        "# CTT Psychometrics\n\n"
        + f"- Cronbach alpha: {report['cronbach_alpha']}\n"
        + f"- Alpha respondents (complete cases): {report['alpha_respondents']}\n\n"
        + f"- Missing response rate: {report['missing_summary']['missing_rate']}\n"
        + f"- Complete-case rate: {report['missing_summary']['complete_case_rate']}\n\n"
        + ("## Warnings\n" + "\n".join(f"- {warning}" for warning in report["warnings"]) + "\n\n" if report["warnings"] else "")
        + table(["Item", "Mean", "SD", "Missing", "Corrected item-total r"], rows)
    )
