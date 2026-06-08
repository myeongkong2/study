from __future__ import annotations

from .models import Project
from .scoring import score_response


def toulmin_argument(project: Project, item_id: str, response: str | None = None) -> dict:
    item = project.item_by_id(item_id)
    claim = next((x for x in project.evidence_claims if x.get("id") == item.get("evidence_claim_id")), {})
    scored = score_response(project, item_id, response) if response is not None else None
    return {
        "claim": claim.get("claim", "The response provides evidence for the targeted KSA."),
        "grounds": {
            "item_stem": item.get("stem"),
            "response": response,
            "score": scored.get("score") if scored else None,
            "variables": item.get("variables"),
        },
        "warrant": "Agreement with the item is treated as ordinal evidence for the linked KSA under the declared scoring direction.",
        "backing": "ECD lineage links construct, KSA, evidence claim, task model, parent template, and response scale.",
        "qualifier": "Pre-operational design-stage interpretation.",
        "rebuttals": [
            "Response style, acquiescence, and social desirability may distort self-report evidence.",
            "Reliability, dimensionality, IRT parameters, and DIF cannot be asserted without pilot data.",
        ],
    }


def toulmin_markdown(argument: dict) -> str:
    return "\n".join(
        [
            "# Toulmin Measurement Argument",
            f"## Claim\n{argument['claim']}",
            f"## Grounds\n- Stem: {argument['grounds']['item_stem']}\n- Response: {argument['grounds']['response']}\n- Score: {argument['grounds']['score']}\n- Variables: {argument['grounds']['variables']}",
            f"## Warrant\n{argument['warrant']}",
            f"## Backing\n{argument['backing']}",
            f"## Qualifier\n{argument['qualifier']}",
            "## Rebuttals\n" + "\n".join(f"- {x}" for x in argument["rebuttals"]),
        ]
    )

