from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def agreement_report(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("ratings", [])
    labels = sorted({row.get("gold") for row in rows} | {row.get("agent") for row in rows})
    total = len(rows)
    matches = sum(1 for row in rows if row.get("gold") == row.get("agent"))
    observed = matches / total if total else 0.0
    gold_counts = Counter(row.get("gold") for row in rows)
    agent_counts = Counter(row.get("agent") for row in rows)
    expected = sum((gold_counts[label] / total) * (agent_counts[label] / total) for label in labels) if total else 0.0
    kappa = (observed - expected) / (1 - expected) if total and expected != 1 else None
    return {
        "ok": True,
        "n": total,
        "accuracy": round(observed, 3),
        "cohen_kappa": round(kappa, 3) if kappa is not None else None,
        "labels": labels,
        "confusion": [
            {"gold": gold, "agent": agent, "count": sum(1 for row in rows if row.get("gold") == gold and row.get("agent") == agent)}
            for gold in labels
            for agent in labels
        ],
    }

