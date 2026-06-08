from __future__ import annotations

import json
from typing import Any


def emit_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def status_mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"

