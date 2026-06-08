from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from ecd_aig.models import load_project
from ecd_aig.validation import validate_project
from ecd_aig.item_quality import audit_project
from ecd_aig.generation import generate_with_validation
from ecd_aig.llm_generation import GeminiRESTClient, generate_llm_candidates
from ecd_aig.blueprint import blueprint_report
from ecd_aig.review import review_status
from ecd_aig.dossier import dossier
from ecd_aig.caf import caf_report
from ecd_aig.toulmin import toulmin_argument
from ecd_aig.scoring import score_response, response_scale_parity
from ecd_aig.response_data import validate_responses
from ecd_aig.psychometrics import psychometrics_report
from ecd_aig.export import export_items
from ecd_aig.agreement import agreement_report
from ecd_aig.simulation import simulation_summary
from ecd_aig.import_items import import_candidate_items
from ecd_aig.pre_response import pre_response_readiness
from ecd_aig.webapp import available_projects, resolve_project

ROOT = Path(__file__).resolve().parents[1]
CONTROLLED = ROOT / "examples" / "job_stress_workload_12item_user_project.json"
RAW = ROOT / "examples" / "job_stress_raw_user_items_project.json"
SAMPLE = ROOT / "examples" / "sample_project.json"
RESPONSES = ROOT / "examples" / "pilot_responses.csv"
RESPONSES_WITH_MISSING = ROOT / "examples" / "pilot_responses_missing.csv"
RESPONSES_WITH_HIGH_MISSING = ROOT / "examples" / "pilot_responses_high_missing.csv"
GOLD = ROOT / "examples" / "gold_set_agreement.json"
IMPORT_WITHOUT_LINEAGE = ROOT / "examples" / "import_candidate_without_lineage.json"


class EcdAigTests(unittest.TestCase):
    def test_load_project(self):
        project = load_project(CONTROLLED)
        self.assertEqual(project.id, "job_stress_workload_12")
        self.assertEqual(len(project.items), 12)

    def test_validate_controlled_project(self):
        self.assertTrue(validate_project(load_project(CONTROLLED))["ok"])

    def test_traceability_gate_detects_relationship_mismatch(self):
        project = load_project(CONTROLLED)
        project.items[0]["ksa_id"] = "ksa_workload_strain"
        report = validate_project(project)
        gate = next(gate for gate in report["gates"] if gate["code"] == "traceability")
        self.assertFalse(gate["ok"])
        self.assertTrue(any("does not match" in problem for problem in gate["problems"]))

    def test_scoring_readiness_gate_detects_missing_direction(self):
        project = load_project(CONTROLLED)
        project.items[0]["scoring"].pop("direction")
        gate = next(gate for gate in validate_project(project)["gates"] if gate["code"] == "scoring_readiness")
        self.assertFalse(gate["ok"])

    def test_redundancy_gate_detects_duplicate_stem(self):
        project = load_project(CONTROLLED)
        project.items[1]["stem"] = project.items[0]["stem"]
        gate = next(gate for gate in validate_project(project)["gates"] if gate["code"] == "redundancy")
        self.assertFalse(gate["ok"])

    def test_sensitivity_gate_detects_watch_list_term(self):
        project = load_project(CONTROLLED)
        project.items[0]["stem"] += " 성별"
        gate = next(gate for gate in validate_project(project)["gates"] if gate["code"] == "sensitivity")
        self.assertFalse(gate["ok"])

    def test_audit_controlled_passes_strict(self):
        report = audit_project(load_project(CONTROLLED), strict=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["screening_type"], "automated_rule_based")
        self.assertGreater(len(report["expert_review_criteria"]), 0)

    def test_audit_raw_fails_strict(self):
        project = load_project(RAW)
        self.assertEqual(len(project.items), 15)
        self.assertFalse(audit_project(project, strict=True)["ok"])

    def test_generation_uses_parent_template(self):
        report = generate_with_validation(load_project(SAMPLE), "tpl_worry_001", 3)
        self.assertTrue(report["ok"])
        self.assertEqual(len(report["items"]), 3)

    def test_llm_generation_assigns_lineage_from_parent_template(self):
        project = load_project(SAMPLE)
        template = project.template_by_id("tpl_worry_001")
        variables = {key: values[0] for key, values in template["variables"].items()}

        class FakeGeminiClient:
            model = "fake-gemini"

            def generate_json(self, prompt, schema):
                self.prompt = prompt
                self.schema = schema
                return {
                    "items": [
                        {
                            "stem": "업무 상황에서 걱정과 긴장을 경험하는 정도를 응답해 주세요",
                            "rationale": "승인된 걱정 반응 구성개념에 맞춘 사전 검토용 후보입니다.",
                            "variables": variables,
                            "construct_id": "hallucinated_construct",
                        }
                    ]
                }

        client = FakeGeminiClient()
        report = generate_llm_candidates(project, "tpl_worry_001", 1, client=client)
        item = report["items"][0]
        self.assertTrue(report["ok"])
        self.assertEqual(item["construct_id"], template["construct_id"])
        self.assertEqual(item["ksa_id"], template["ksa_id"])
        self.assertEqual(item["parent_template_id"], template["id"])
        self.assertEqual(item["status"], "llm_generated_candidate")
        self.assertIn("Do not create or return lineage IDs", client.prompt)

    def test_llm_generation_accepts_proposed_variable_value_for_expert_review(self):
        project = load_project(SAMPLE)
        template = project.template_by_id("tpl_worry_001")
        variables = {key: values[0] for key, values in template["variables"].items()}
        variables["work_situation"] = "승인되지 않은 상황"

        class FakeGeminiClient:
            model = "fake-gemini"

            def generate_json(self, prompt, schema):
                return {"items": [{"stem": "충분히 긴 후보 문항입니다", "rationale": "후보", "variables": variables}]}

        report = generate_llm_candidates(project, "tpl_worry_001", 1, client=FakeGeminiClient())
        self.assertEqual(len(report["items"]), 1)
        self.assertEqual(report["task_feature_values"], "llm_proposed_for_expert_review")
        self.assertEqual(report["items"][0]["variables"]["work_situation"], variables["work_situation"])

    def test_llm_generation_rejects_repeated_variable_combination(self):
        project = load_project(SAMPLE)
        template = project.template_by_id("tpl_worry_001")
        variables = {key: values[0] for key, values in template["variables"].items()}

        class FakeGeminiClient:
            model = "fake-gemini"

            def generate_json(self, prompt, schema):
                count = schema["properties"]["items"]["maxItems"]
                return {"items": [{"stem": f"후보 문항 {index}입니다.", "rationale": "후보", "variables": variables} for index in range(count)]}

        with self.assertRaisesRegex(ValueError, "returned only 1 unique candidate"):
            generate_llm_candidates(project, "tpl_worry_001", 2, client=FakeGeminiClient())

    def test_llm_generation_rejects_repeated_stem(self):
        project = load_project(SAMPLE)
        template = project.template_by_id("tpl_worry_001")
        variable_keys = list(template["variables"])
        first = {key: template["variables"][key][0] for key in variable_keys}
        second = dict(first)
        second[variable_keys[-1]] = template["variables"][variable_keys[-1]][1]

        class FakeGeminiClient:
            model = "fake-gemini"

            def generate_json(self, prompt, schema):
                count = schema["properties"]["items"]["maxItems"]
                values = [first, second]
                return {"items": [{"stem": "같은 후보 문항입니다.", "rationale": "후보", "variables": values[index % 2]} for index in range(count)]}

        with self.assertRaisesRegex(ValueError, "returned only 1 unique candidate"):
            generate_llm_candidates(project, "tpl_worry_001", 2, client=FakeGeminiClient())

    def test_llm_generation_retries_only_missing_unique_candidates(self):
        project = load_project(SAMPLE)
        project.items.append(
            {
                "id": "LLM-001",
                "parent_template_id": "tpl_worry_001",
                "variables": {"work_situation": "기존 상황", "negative_response": "기존 반응"},
                "stem": "나는 기존 상황에서 기존 반응을 느낀다.",
            }
        )

        class FakeGeminiClient:
            model = "fake-gemini"

            def __init__(self):
                self.calls = 0

            def generate_json(self, prompt, schema):
                self.calls += 1
                if self.calls == 1:
                    return {
                        "items": [
                            {"stem": "나는 기존 상황에서 기존 반응을 느낀다.", "rationale": "중복", "variables": {"work_situation": "기존 상황", "negative_response": "기존 반응"}},
                            {"stem": "나는 새로운 상황 하나에서 긴장감을 느낀다.", "rationale": "후보", "variables": {"work_situation": "새로운 상황 하나", "negative_response": "긴장감"}},
                        ]
                    }
                return {
                    "items": [
                        {"stem": "나는 새로운 상황 둘에서 부담감을 느낀다.", "rationale": "후보", "variables": {"work_situation": "새로운 상황 둘", "negative_response": "부담감"}}
                    ]
                }

        client = FakeGeminiClient()
        report = generate_llm_candidates(project, "tpl_worry_001", 2, client=client)
        self.assertEqual(client.calls, 2)
        self.assertEqual(len(report["items"]), 2)

    def test_llm_generation_can_expand_task_features_without_json_edit(self):
        project = load_project(SAMPLE)

        class FakeGeminiClient:
            model = "fake-gemini"

            def generate_json(self, prompt, schema):
                self.prompt = prompt
                return {
                    "items": [
                        {
                            "stem": f"나는 업무 상황 {index}에서 긴장 반응 {index}을 느낀다.",
                            "rationale": "LLM 제안 변수는 전문가 검토 대상이다.",
                            "variables": {
                                "work_situation": f"업무 상황 {index}",
                                "negative_response": f"긴장 반응 {index}",
                            },
                        }
                        for index in range(1, 21)
                    ]
                }

        client = FakeGeminiClient()
        report = generate_llm_candidates(project, "tpl_worry_001", 20, client=client, brief="서로 다른 업무 상황을 폭넓게 제안")
        self.assertEqual(len(report["items"]), 20)
        self.assertEqual(report["task_feature_values"], "llm_proposed_for_expert_review")
        self.assertIn("서로 다른 업무 상황을 폭넓게 제안", client.prompt)

    def test_gemini_client_requires_environment_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                GeminiRESTClient(api_key="")

    def test_blueprint_counts_items(self):
        report = blueprint_report(load_project(CONTROLLED))
        self.assertEqual(report["by_ksa"]["ksa_deadline_pressure"], 4)

    def test_review_status_detects_missing_decisions(self):
        report = review_status(load_project(CONTROLLED))
        self.assertFalse(report["ok"])
        self.assertGreater(len(report["problems"]), 0)

    def test_dossier_contains_boundary(self):
        report = dossier(load_project(CONTROLLED), "JS-WB-012", "E")
        self.assertIn("boundary", report)
        self.assertEqual(report["toulmin"]["grounds"]["score"], 5)

    def test_caf_contains_four_process(self):
        report = caf_report(load_project(CONTROLLED))
        self.assertIn("response_processing", report["four_process_architecture"])

    def test_toulmin_argument_scores_response(self):
        report = toulmin_argument(load_project(CONTROLLED), "JS-WB-012", "E")
        self.assertEqual(report["grounds"]["score"], 5)

    def test_score_letter_response(self):
        report = score_response(load_project(CONTROLLED), "JS-WB-001", "A")
        self.assertEqual(report["score"], 1)

    def test_scale_parity(self):
        self.assertTrue(response_scale_parity(load_project(CONTROLLED))["ok"])

    def test_response_validation(self):
        report = validate_responses(load_project(CONTROLLED), RESPONSES)
        self.assertTrue(report["ok"])
        self.assertEqual(report["respondents"], 8)

    def test_psychometrics_alpha(self):
        report = psychometrics_report(load_project(CONTROLLED), str(RESPONSES))
        self.assertIsNotNone(report["cronbach_alpha"])
        self.assertLessEqual(report["cronbach_alpha"], 1)
        self.assertEqual(report["alpha_respondents"], 8)
        self.assertEqual(len(report["items"]), 12)

    def test_psychometrics_preserves_row_alignment_with_missing_response(self):
        report = psychometrics_report(load_project(CONTROLLED), str(RESPONSES_WITH_MISSING))
        correlations = [item["corrected_item_total_corr"] for item in report["items"] if item["corrected_item_total_corr"] is not None]
        self.assertEqual(report["alpha_respondents"], 7)
        self.assertTrue(all(-1 <= value <= 1 for value in correlations))
        first_item = next(item for item in report["items"] if item["item_id"] == "JS-WB-001")
        self.assertEqual(first_item["missing"], 1)

    def test_psychometrics_warns_when_missingness_is_high(self):
        report = psychometrics_report(load_project(CONTROLLED), str(RESPONSES_WITH_HIGH_MISSING))
        self.assertGreater(len(report["warnings"]), 0)
        self.assertLess(report["missing_summary"]["complete_case_rate"], 0.8)

    def test_export_formats(self):
        project = load_project(CONTROLLED)
        tmp = ROOT / "outputs" / "test_exports"
        tmp.mkdir(parents=True, exist_ok=True)
        for fmt, name in [("csv", "items.csv"), ("json", "items.json"), ("lms-json", "lms.json"), ("qti-lite", "items.xml")]:
            out = tmp / name
            report = export_items(project, out, fmt)
            self.assertTrue(report["ok"])
            self.assertTrue(out.exists())
            if fmt == "qti-lite":
                self.assertFalse(report["production_lms_ready"])
                self.assertEqual(report["profile"], "prototype_qti_lite")

    def test_agreement_report(self):
        report = agreement_report(GOLD)
        self.assertEqual(report["n"], 8)
        self.assertIn("cohen_kappa", report)

    def test_simulation_summary(self):
        report = simulation_summary(load_project(CONTROLLED))
        self.assertEqual(report["current_items"], 12)
        self.assertEqual(report["total_possible_combinations"], 48)

    def test_pre_response_report_states_empirical_boundary(self):
        report = pre_response_readiness(load_project(CONTROLLED))
        self.assertEqual(report["report_type"], "pre_response_readiness")
        self.assertIn("does not establish empirical", report["validity_boundary"])
        self.assertIn("DIF and empirical fairness analysis", report["requires_response_data"])

    def test_import_does_not_invent_measurement_lineage(self):
        report = validate_project(import_candidate_items(IMPORT_WITHOUT_LINEAGE))
        self.assertFalse(report["ok"])
        traceability = next(gate for gate in report["gates"] if gate["code"] == "traceability")
        self.assertTrue(any("missing/unknown construct_id" in problem for problem in traceability["problems"]))

    def test_webapp_project_resolution_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            resolve_project("../README.md")

    def test_webapp_lists_only_item_projects(self):
        projects = available_projects()
        self.assertIn("sample_project.json", projects)
        self.assertNotIn("gold_set_agreement.json", projects)


if __name__ == "__main__":
    unittest.main()
