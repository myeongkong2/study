from __future__ import annotations

from collections import Counter, defaultdict
from .models import Project
from .rendering import table


def blueprint_report(project: Project) -> dict:
    by_ksa = Counter(item.get("ksa_id") for item in project.items)
    by_template = Counter(item.get("parent_template_id") for item in project.items)
    coverage = []
    for template in project.parent_templates:
        template_id = template.get("id")
        allowed = template.get("variables") or {}
        seen_by_var: dict[str, set] = defaultdict(set)
        for item in project.items:
            if item.get("parent_template_id") == template_id:
                for key, value in (item.get("variables") or {}).items():
                    seen_by_var[key].add(value)
        for var, values in allowed.items():
            seen = seen_by_var[var]
            coverage.append(
                {
                    "template_id": template_id,
                    "variable": var,
                    "allowed": values,
                    "seen": sorted(seen),
                    "missing": [value for value in values if value not in seen],
                }
            )
    return {"by_ksa": dict(by_ksa), "by_template": dict(by_template), "coverage": coverage}


def blueprint_markdown(report: dict) -> str:
    sections = ["# Blueprint Coverage"]
    sections.append("\n## KSA Counts\n" + table(["KSA", "Items"], [[k, v] for k, v in sorted(report["by_ksa"].items())]))
    sections.append("\n## Parent Template Counts\n" + table(["Template", "Items"], [[k, v] for k, v in sorted(report["by_template"].items())]))
    rows = [[x["template_id"], x["variable"], len(x["seen"]), ", ".join(x["missing"]) or "-"] for x in report["coverage"]]
    sections.append("\n## Task Variable Coverage\n" + table(["Template", "Variable", "Seen", "Missing"], rows))
    return "\n".join(sections)

