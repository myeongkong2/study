from __future__ import annotations

from .models import Project

LETTER_TO_SCORE = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


def parse_response(response: str, project: Project) -> int:
    response = str(response).strip()
    if response.upper() in LETTER_TO_SCORE:
        return LETTER_TO_SCORE[response.upper()]
    try:
        return int(response)
    except ValueError:
        pass
    for anchor in project.response_scale.get("anchors", []):
        if response == str(anchor.get("label")):
            return int(anchor["score"])
    raise ValueError(f"unknown response: {response}")


def score_response(project: Project, item_id: str, response: str) -> dict:
    item = project.item_by_id(item_id)
    raw = parse_response(response, project)
    scores = [int(a["score"]) for a in project.response_scale.get("anchors", [])]
    if raw not in scores:
        raise ValueError(f"response score outside scale: {raw}")
    direction = (item.get("scoring") or {}).get("direction", "positive")
    score = max(scores) + min(scores) - raw if direction == "reverse" else raw
    return {"item_id": item_id, "response": response, "raw_score": raw, "score": score, "direction": direction}


def response_scale_parity(project: Project) -> dict:
    scores = [a.get("score") for a in project.response_scale.get("anchors", [])]
    expected = list(range(min(scores), max(scores) + 1)) if scores else []
    return {"ok": scores == expected, "scores": scores, "expected": expected}

