from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


def _list(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


@dataclass
class Project:
    id: str
    title: str
    constructs: list[dict[str, Any]] = field(default_factory=list)
    ksas: list[dict[str, Any]] = field(default_factory=list)
    evidence_claims: list[dict[str, Any]] = field(default_factory=list)
    task_models: list[dict[str, Any]] = field(default_factory=list)
    parent_templates: list[dict[str, Any]] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    response_scale: dict[str, Any] = field(default_factory=dict)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        return cls(
            id=str(data.get("id", "project")),
            title=str(data.get("title", "Untitled ECD-AIG Project")),
            constructs=_list(data.get("constructs")),
            ksas=_list(data.get("ksas")),
            evidence_claims=_list(data.get("evidence_claims")),
            task_models=_list(data.get("task_models")),
            parent_templates=_list(data.get("parent_templates")),
            items=_list(data.get("items")),
            response_scale=data.get("response_scale") or {},
            reviews=_list(data.get("reviews")),
            metadata=data.get("metadata") or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "constructs": self.constructs,
            "ksas": self.ksas,
            "evidence_claims": self.evidence_claims,
            "task_models": self.task_models,
            "parent_templates": self.parent_templates,
            "items": self.items,
            "response_scale": self.response_scale,
            "reviews": self.reviews,
            "metadata": self.metadata,
        }

    def ids(self, collection: str) -> set[str]:
        return {str(x.get("id")) for x in getattr(self, collection) if x.get("id")}

    def item_by_id(self, item_id: str) -> dict[str, Any]:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        raise KeyError(f"unknown item id: {item_id}")

    def template_by_id(self, template_id: str) -> dict[str, Any]:
        for template in self.parent_templates:
            if template.get("id") == template_id:
                return template
        raise KeyError(f"unknown template id: {template_id}")


def load_project(path: str | Path) -> Project:
    with Path(path).open("r", encoding="utf-8") as handle:
        return Project.from_dict(json.load(handle))


def save_project(project: Project, path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(project.to_dict(), handle, ensure_ascii=False, indent=2)


def result(ok: bool, code: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"ok": ok, "code": code, "message": message}
    payload.update(extra)
    return payload