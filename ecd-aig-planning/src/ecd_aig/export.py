from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from .models import Project

QTI_LITE_NOTICE = (
    "qti-lite is a prototype XML interchange format. "
    "It is not certified as a complete IMS QTI package for LMS production use."
)


def item_records(project: Project) -> list[dict]:
    records = []
    for item in project.items:
        records.append(
            {
                "id": item.get("id"),
                "stem": item.get("stem"),
                "response_scale": project.response_scale.get("type"),
                "options": json.dumps(project.response_scale.get("anchors", []), ensure_ascii=False),
                "variables": json.dumps(item.get("variables", {}), ensure_ascii=False),
                "construct_id": item.get("construct_id"),
                "ksa_id": item.get("ksa_id"),
                "evidence_claim_id": item.get("evidence_claim_id"),
                "parent_template_id": item.get("parent_template_id"),
                "status": item.get("status", ""),
            }
        )
    return records


def export_items(project: Project, out: str | Path, fmt: str) -> dict:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = item_records(project)
    if fmt == "csv":
        with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()) if records else ["id"])
            writer.writeheader()
            writer.writerows(records)
    elif fmt in {"json", "lms-json"}:
        payload = {"project": {"id": project.id, "title": project.title}, "items": records}
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif fmt == "qti-lite":
        root = Element("questestinterop")
        for item in project.items:
            item_el = SubElement(root, "item", ident=item.get("id", ""))
            SubElement(item_el, "presentation").text = item.get("stem", "")
            response = SubElement(item_el, "response_lid", ident="likert")
            for anchor in project.response_scale.get("anchors", []):
                SubElement(response, "response_label", ident=str(anchor.get("score"))).text = str(anchor.get("label"))
        out_path.write_text(tostring(root, encoding="unicode"), encoding="utf-8")
    else:
        raise ValueError(f"unknown export format: {fmt}")
    report = {"ok": True, "out": str(out_path), "format": fmt, "items": len(records)}
    if fmt == "qti-lite":
        report.update({"profile": "prototype_qti_lite", "production_lms_ready": False, "notice": QTI_LITE_NOTICE})
    elif fmt == "lms-json":
        report.update({"profile": "prototype_lms_json", "production_lms_ready": False})
    return report
