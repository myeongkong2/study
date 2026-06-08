from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .item_quality import audit_project
from .models import Project
from .validation import validate_project

DEFAULT_MODEL = "gemini-2.5-flash"
PROVIDER = "google_ai_studio_gemini"
PROMPT_VERSION = "ecd-aig-llm-generation-v2"


class JsonGenerationClient(Protocol):
    model: str

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        ...


class GeminiAPIError(RuntimeError):
    """Raised when Gemini cannot return a usable structured response."""


class GeminiRESTClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Set the Google AI Studio API key in the environment before running llm-generate."
            )
        self.model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
        self.timeout = timeout

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        model = quote(self.model, safe="-._")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GeminiAPIError(f"Gemini API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise GeminiAPIError(f"Gemini API connection failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise GeminiAPIError("Gemini API returned invalid JSON.") from exc

        try:
            text = raw["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiAPIError(f"Gemini API response has no generated JSON text: {raw}") from exc
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiAPIError(f"Gemini structured output is not valid JSON: {text}") from exc


def _generation_schema(count: int, variable_keys: list[str]) -> dict[str, Any]:
    variable_properties = {key: {"type": "string"} for key in variable_keys}
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "properties": {
                        "stem": {"type": "string"},
                        "rationale": {"type": "string"},
                        "variables": {
                            "type": "object",
                            "properties": variable_properties,
                            "required": variable_keys,
                        },
                    },
                    "required": ["stem", "rationale", "variables"],
                },
            }
        },
        "required": ["items"],
    }


def _variable_tuple(variables: dict[str, Any], keys: list[str]) -> tuple[Any, ...]:
    return tuple(variables.get(key) for key in keys)


def _normalize_stem(stem: str) -> str:
    return re.sub(r"\s+", "", stem).lower()


def build_generation_prompt(
    project: Project,
    template: dict[str, Any],
    count: int,
    brief: str | None = None,
    excluded_combinations: list[dict[str, Any]] | None = None,
    excluded_stems: list[str] | None = None,
) -> str:
    lineage = {
        "construct_id": template.get("construct_id"),
        "ksa_id": template.get("ksa_id"),
        "evidence_claim_id": template.get("evidence_claim_id"),
        "task_model_id": template.get("task_model_id"),
        "parent_template_id": template.get("id"),
    }
    prompt_context = {
        "project_title": project.title,
        "lineage": lineage,
        "stem_template": template.get("stem_template"),
        "template_rationale": template.get("rationale", ""),
        "example_variables": template.get("variables") or {},
        "user_brief": brief or "",
        "excluded_variable_combinations": excluded_combinations or [],
        "excluded_stems": excluded_stems or [],
        "response_scale": project.response_scale,
        "candidate_count": count,
    }
    return (
        "You generate candidate assessment items for expert review before pilot administration.\n"
        "Generate exactly the requested number of items in Korean.\n"
        "Preserve the intended construct and evidence claim. Use one situation and one response signal per item.\n"
        "Use the variable keys from example_variables, but propose new context-appropriate values when needed for diversity.\n"
        "Return every listed variable key. Use a different variable combination for every item. Do not repeat a stem.\n"
        "Do not reuse any excluded_variable_combinations or excluded_stems.\n"
        "Treat variable values as LLM-proposed task-feature candidates for expert review, not as approved evidence.\n"
        "Do not create or return lineage IDs. The application assigns lineage from the approved parent template.\n"
        "Do not claim empirical validity, reliability, IRT calibration, or DIF evidence.\n"
        "Return only the JSON structure requested by the response schema.\n\n"
        f"Approved generation context:\n{json.dumps(prompt_context, ensure_ascii=False, indent=2)}"
    )


def _validated_candidates(
    project: Project,
    template: dict[str, Any],
    payload: dict[str, Any],
    count: int,
    accepted_combinations: set[tuple[Any, ...]] | None = None,
    accepted_stems: set[str] | None = None,
) -> list[dict[str, Any]]:
    candidates = payload.get("items")
    if not isinstance(candidates, list) or len(candidates) != count:
        raise ValueError(f"Gemini must return exactly {count} candidate item(s).")
    allowed_variables = template.get("variables") or {}
    expected_keys = set(allowed_variables)
    variable_keys = list(allowed_variables)
    existing_stems = {_normalize_stem(item.get("stem", "")) for item in project.items if item.get("stem")}
    existing_combinations = {
        _variable_tuple(item.get("variables") or {}, variable_keys)
        for item in project.items
        if item.get("parent_template_id") == template.get("id")
    }
    seen_combinations = set(accepted_combinations or set())
    seen_stems = set(accepted_stems or set())
    validated = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise ValueError(f"Gemini candidate {index} must be an object.")
        stem = candidate.get("stem")
        rationale = candidate.get("rationale")
        variables = candidate.get("variables")
        if not isinstance(stem, str) or not stem.strip():
            raise ValueError(f"Gemini candidate {index} has no usable stem.")
        if not isinstance(rationale, str):
            raise ValueError(f"Gemini candidate {index} rationale must be text.")
        if not isinstance(variables, dict) or set(variables) != expected_keys:
            raise ValueError(f"Gemini candidate {index} must return exactly these variables: {sorted(expected_keys)}.")
        combination = _variable_tuple(variables, variable_keys)
        if combination in existing_combinations:
            continue
        if combination in seen_combinations:
            continue
        normalized_stem = _normalize_stem(stem)
        if normalized_stem in existing_stems:
            continue
        if normalized_stem in seen_stems:
            continue
        seen_combinations.add(combination)
        seen_stems.add(normalized_stem)
        validated.append({"stem": stem.strip(), "rationale": rationale.strip(), "variables": variables})
    return validated


def _next_item_ids(project: Project, count: int) -> list[str]:
    used = project.ids("items")
    item_ids = []
    sequence = 1
    while len(item_ids) < count:
        candidate = f"LLM-{sequence:03d}"
        if candidate not in used:
            item_ids.append(candidate)
        sequence += 1
    return item_ids


def generate_llm_candidates(
    project: Project,
    template_id: str,
    count: int,
    client: JsonGenerationClient | None = None,
    model: str | None = None,
    brief: str | None = None,
    max_attempts: int = 4,
) -> dict[str, Any]:
    if count < 1:
        raise ValueError("count must be at least 1.")
    template = project.template_by_id(template_id)
    active_client = client or GeminiRESTClient(model=model)
    variable_keys = list((template.get("variables") or {}).keys())
    existing_items = [item for item in project.items if item.get("parent_template_id") == template_id]
    excluded_combinations = [item.get("variables") or {} for item in existing_items]
    excluded_stems = [item.get("stem", "") for item in existing_items if item.get("stem")]
    accepted_combinations: set[tuple[Any, ...]] = set()
    accepted_stems: set[str] = set()
    candidates = []
    prompts = []
    for _attempt in range(1, max_attempts + 1):
        remaining = count - len(candidates)
        if remaining == 0:
            break
        prompt = build_generation_prompt(
            project,
            template,
            remaining,
            brief=brief,
            excluded_combinations=excluded_combinations + [candidate["variables"] for candidate in candidates],
            excluded_stems=excluded_stems + [candidate["stem"] for candidate in candidates],
        )
        prompts.append(prompt)
        schema = _generation_schema(remaining, variable_keys)
        payload = active_client.generate_json(prompt, schema)
        batch = _validated_candidates(
            project,
            template,
            payload,
            remaining,
            accepted_combinations=accepted_combinations,
            accepted_stems=accepted_stems,
        )
        candidates.extend(batch)
        accepted_combinations.update(_variable_tuple(candidate["variables"], variable_keys) for candidate in batch)
        accepted_stems.update(_normalize_stem(candidate["stem"]) for candidate in batch)
    if len(candidates) != count:
        raise ValueError(
            f"Gemini returned only {len(candidates)} unique candidate(s) after {max_attempts} attempt(s); "
            f"{count} were requested. Try a more specific --brief or request a smaller count."
        )
    generated_at = datetime.now(timezone.utc).isoformat()
    prompt_sha256 = hashlib.sha256("\n\n".join(prompts).encode("utf-8")).hexdigest()
    score_values = [anchor["score"] for anchor in project.response_scale.get("anchors", []) if "score" in anchor]

    items = []
    for item_id, candidate in zip(_next_item_ids(project, count), candidates):
        items.append(
            {
                "id": item_id,
                "construct_id": template.get("construct_id"),
                "ksa_id": template.get("ksa_id"),
                "evidence_claim_id": template.get("evidence_claim_id"),
                "task_model_id": template.get("task_model_id"),
                "parent_template_id": template_id,
                "variables": candidate["variables"],
                "stem": candidate["stem"],
                "rationale": candidate["rationale"],
                "scoring": {"direction": "positive", "valid_scores": score_values},
                "status": "llm_generated_candidate",
                "generation": {
                    "provider": PROVIDER,
                    "model": active_client.model,
                    "prompt_version": PROMPT_VERSION,
                    "prompt_sha256": prompt_sha256,
                    "generated_at": generated_at,
                    "task_feature_values": "llm_proposed_for_expert_review",
                },
            }
        )

    probe = Project.from_dict(project.to_dict())
    probe.items = project.items + items
    validation = validate_project(probe)
    item_quality = audit_project(probe, strict=True)
    return {
        "ok": validation["ok"] and item_quality["ok"],
        "provider": PROVIDER,
        "model": active_client.model,
        "prompt_version": PROMPT_VERSION,
        "task_feature_values": "llm_proposed_for_expert_review",
        "items": items,
        "validation": validation,
        "item_quality": item_quality,
        "validity_boundary": (
            "LLM output is a pre-response candidate set for structural screening and expert review. "
            "It is not empirical validity evidence."
        ),
    }
