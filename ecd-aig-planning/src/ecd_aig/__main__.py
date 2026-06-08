from __future__ import annotations

import argparse
from .models import load_project, save_project
from .rendering import emit_json, table
from .validation import validate_project
from .item_quality import audit_project, audit_markdown
from .generation import generate_with_validation
from .llm_generation import GeminiAPIError, generate_llm_candidates
from .import_items import import_candidate_items
from .blueprint import blueprint_report, blueprint_markdown
from .review import review_status, review_markdown
from .dossier import dossier, dossier_markdown
from .caf import caf_report, caf_markdown
from .toulmin import toulmin_argument, toulmin_markdown
from .scoring import score_response, response_scale_parity
from .response_data import validate_responses
from .psychometrics import psychometrics_report, psychometrics_markdown
from .export import export_items
from .agreement import agreement_report
from .simulation import simulation_summary
from .pre_response import pre_response_readiness, pre_response_markdown
from . import webapp


def print_report(data, markdown: str | None, args) -> None:
    if getattr(args, "markdown", False) and markdown is not None:
        print(markdown)
    elif getattr(args, "json", False):
        print(emit_json(data))
    else:
        print(emit_json(data))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ecd_aig")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def project_arg(name: str):
        p = sub.add_parser(name)
        p.add_argument("project")
        p.add_argument("--json", action="store_true")
        p.add_argument("--markdown", action="store_true")
        return p

    project_arg("validate")
    project_arg("pre-response")
    audit = project_arg("audit-items")
    audit.add_argument("--strict", action="store_true")

    imp = sub.add_parser("import-items")
    imp.add_argument("candidate_json")
    imp.add_argument("--out", required=True)
    imp.add_argument("--json", action="store_true")

    gen = project_arg("generate")
    gen.add_argument("--template", required=True)
    gen.add_argument("--count", type=int, default=1)
    gen.add_argument("--write", action="store_true")

    llm_gen = project_arg("llm-generate")
    llm_gen.add_argument("--template", required=True)
    llm_gen.add_argument("--count", type=int, default=1)
    llm_gen.add_argument("--model")
    llm_gen.add_argument("--brief", help="Natural-language guidance for diverse candidate generation.")
    llm_gen.add_argument("--write", action="store_true")

    project_arg("blueprint")
    project_arg("review-status")

    dos = project_arg("dossier")
    dos.add_argument("--item")
    dos.add_argument("--response")

    caf = project_arg("caf")
    sub.add_parser("ecd-map", parents=[caf], add_help=False)

    tou = project_arg("toulmin")
    tou.add_argument("--item", required=True)
    tou.add_argument("--response")

    score = project_arg("score")
    score.add_argument("--item", required=True)
    score.add_argument("--response", required=True)

    resp = project_arg("responses")
    resp.add_argument("csv")

    psy = project_arg("psychometrics")
    psy.add_argument("csv")

    exp = project_arg("export-items")
    exp.add_argument("--out", required=True)
    exp.add_argument("--format", choices=["csv", "json", "lms-json", "qti-lite"], required=True)

    parity = project_arg("scale-parity")

    sim = project_arg("simulation")

    agree = sub.add_parser("agreement")
    agree.add_argument("gold_set")
    agree.add_argument("--json", action="store_true")

    web = sub.add_parser("webapp")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)

    if args.cmd == "webapp":
        webapp.run(args.host, args.port)
        return 0

    if args.cmd == "import-items":
        project = import_candidate_items(args.candidate_json)
        save_project(project, args.out)
        print(emit_json({"ok": True, "out": args.out, "items": len(project.items)}))
        return 0

    if args.cmd == "agreement":
        print(emit_json(agreement_report(args.gold_set)))
        return 0

    project = load_project(args.project)

    if args.cmd == "validate":
        data = validate_project(project)
        print_report(data, validation_markdown(data), args)
    elif args.cmd == "pre-response":
        data = pre_response_readiness(project)
        print_report(data, pre_response_markdown(data), args)
    elif args.cmd == "audit-items":
        data = audit_project(project, strict=args.strict)
        print_report(data, audit_markdown(data), args)
    elif args.cmd == "generate":
        data = generate_with_validation(project, args.template, args.count)
        if args.write:
            project.items.extend(data["items"])
            save_project(project, args.project)
        print_report(data, generated_markdown(data), args)
    elif args.cmd == "llm-generate":
        try:
            data = generate_llm_candidates(project, args.template, args.count, model=args.model, brief=args.brief)
        except (GeminiAPIError, ValueError) as exc:
            parser.error(str(exc))
        if args.write:
            if not data["ok"]:
                raise ValueError("LLM candidates did not pass the pre-response gates and were not written.")
            project.items.extend(data["items"])
            save_project(project, args.project)
        print_report(data, generated_markdown(data), args)
    elif args.cmd == "blueprint":
        data = blueprint_report(project)
        print_report(data, blueprint_markdown(data), args)
    elif args.cmd == "review-status":
        data = review_status(project)
        print_report(data, review_markdown(data), args)
    elif args.cmd == "dossier":
        data = dossier(project, args.item, args.response)
        print_report(data, dossier_markdown(data), args)
    elif args.cmd in {"caf", "ecd-map"}:
        data = caf_report(project)
        print_report(data, caf_markdown(data), args)
    elif args.cmd == "toulmin":
        data = toulmin_argument(project, args.item, args.response)
        print_report(data, toulmin_markdown(data), args)
    elif args.cmd == "score":
        data = score_response(project, args.item, args.response)
        print_report(data, None, args)
    elif args.cmd == "responses":
        data = validate_responses(project, args.csv)
        print_report(data, None, args)
    elif args.cmd == "psychometrics":
        data = psychometrics_report(project, args.csv)
        print_report(data, psychometrics_markdown(data), args)
    elif args.cmd == "export-items":
        data = export_items(project, args.out, args.format)
        print_report(data, None, args)
    elif args.cmd == "scale-parity":
        data = response_scale_parity(project)
        print_report(data, None, args)
    elif args.cmd == "simulation":
        data = simulation_summary(project)
        print_report(data, None, args)
    return 0


def validation_markdown(data: dict) -> str:
    rows = [[gate["code"], "PASS" if gate["ok"] else "FAIL", gate["message"]] for gate in data["gates"]]
    return "# Validation Gates\n\n" + table(["Gate", "Status", "Message"], rows)


def generated_markdown(data: dict) -> str:
    rows = [[item["id"], item["stem"]] for item in data["items"]]
    return "# Generated Items\n\n" + table(["Item", "Stem"], rows)


if __name__ == "__main__":
    raise SystemExit(main())
