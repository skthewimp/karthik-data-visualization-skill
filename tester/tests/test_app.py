from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tester.app import create_app


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class TesterApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "runtime"
        self.client = TestClient(create_app(self.root, runner_enabled=False))

    def tearDown(self) -> None:
        self.client.close()
        self.temp.cleanup()

    def create_case(self, **fields: object) -> dict:
        data = {
            "request": "Repair this chart",
            "audience": "Board members",
            "purpose": "Compare sector performance",
            "max_iterations": "3",
            **{name: str(value) for name, value in fields.items()},
        }
        response = self.client.post(
            "/api/cases",
            data=data,
            files={"chart": ("chart.png", PNG_1X1, "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def record_semantic_preflight(self, case_id: str) -> dict:
        case = self.client.get(f"/api/cases/{case_id}").json()
        if case["state"] == "critique":
            critique = {
                "context_version": case["context_version"],
                "apparent_question": "What comparison does the chart support?",
                "apparent_claim": "The visible comparison is the apparent claim",
                "evidence_limitations": ["Source fidelity only"],
                "source_inventory": {
                    "structure": ["One source chart"],
                    "required_content": ["Visible labels and values"],
                    "semantic_mappings": ["Existing label-to-mark mappings"],
                    "uncertainties": [],
                },
                "layout_risks": ["Crowded labels at delivery size"],
                "findings": {
                    "fatal": [],
                    "major": [{"id": "c1", "problem": "Comparison is unclear", "reader_consequence": "Reader effort", "observable_condition": "Comparison is explicit"}],
                    "minor": [
                        {"id": "c2", "problem": "Spacing needs review", "reader_consequence": "Crowding", "observable_condition": "Spacing passes"},
                        {"id": "c3", "problem": "Copy needs review", "reader_consequence": "Weak claim", "observable_condition": "Copy passes"},
                    ],
                },
                "highest_consequence_findings": ["c1", "c2", "c3"],
                "misleading_reader_interpretation": "An unsupported claim",
                "defensible_interpretation": "The visible comparison only",
                "intervention": "repair",
                "form_questioned": False,
                "required_delivered_outcomes": ["Comparison is explicit"],
                "preserve": [],
            }
            response = self.client.post(f"/api/cases/{case_id}/critique", json={"report": critique})
            self.assertEqual(response.status_code, 200, response.text)
            critique_number = response.json()["critiques"][-1]["number"]
            design = {
                "critique_number": critique_number,
                "requirements": [{"finding_id": "c1", "planned_change": "Clarify comparison", "affected_zones": ["plot"], "observable_outcome": "Comparison is explicit"}],
                "measure_scope": "Visible measure",
                "evidence_scope": "Source fidelity",
                "chart_form": "Existing form",
                "primary_identification": "Existing labels",
                "zones": {name: name for name in ("title", "subtitle", "legend", "plot", "annotation", "footer")},
                "colour_role": "Identity only",
                "dimensions": {"width": 1200, "height": 675},
                "value_precision": "exact",
                "selector_decision": None,
                "preservation_plan": [
                    {
                        "source_item": "Visible labels and values",
                        "planned_treatment": "Carry them into the repair",
                        "observable_outcome": "All remain identifiable",
                    },
                    {
                        "source_item": "Existing label-to-mark mappings",
                        "planned_treatment": "Preserve identities",
                        "observable_outcome": "Labels remain bound to the correct marks",
                    },
                ],
                "layout_plan": {
                    "delivery_size": "1200 by 675 pixels",
                    "longest_text": "Measure the longest label",
                    "dense_regions": "Inspect title, plot, and footer",
                    "collision_risks": ["Labels could collide at delivery size"],
                    "mitigation": "Reserve space before plotting",
                    "preview_check": "Inspect the complete delivery-size export",
                },
                "plan_audit": {
                    "verdict": "Ready",
                    "summary": "The plan covers the source and predictable risks",
                    "inventory_coverage": "Pass",
                    "diagnosis_coverage": "Pass",
                    "preservation_coverage": "Pass",
                    "layout_coverage": "Pass",
                    "required_plan_changes": [],
                },
            }
            response = self.client.post(f"/api/cases/{case_id}/design-contract", json={"report": design})
            self.assertEqual(response.status_code, 200, response.text)
            renderer = {
                "requested": "matplotlib",
                "selected": "matplotlib",
                "ggplot2_supported": True,
                "reason": "Explicit test renderer",
                "probe": {"renderers": {"ggplot2": {"available": True}, "matplotlib": {"available": True}}},
            }
            response = self.client.post(f"/api/cases/{case_id}/renderer-selection", json={"report": renderer})
            self.assertEqual(response.status_code, 200, response.text)
        payload = {
            name: {
                "result": "clear",
                "observed": f"Observed {name}",
                "risk": f"Risk assessed for {name}",
                "required": f"Required state for {name}",
            }
            for name in (
                "measure",
                "time_context",
                "universe_denominator",
                "claim_strength",
                "audience_units",
            )
        }
        response = self.client.post(
            f"/api/cases/{case_id}/semantic-preflight", json=payload
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_health_marks_console_as_not_a_provider_runner(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider_runner"], False)

    def test_disabled_local_runner_cannot_start_a_job(self) -> None:
        case = self.create_case()
        response = self.client.post(f"/api/cases/{case['case_id']}/run")
        self.assertEqual(response.status_code, 503)
        self.assertIn("DATAVIZ_ENABLE_LOCAL_RUNNER", response.json()["detail"])

        missing = self.client.get("/api/jobs/" + "0" * 32)
        self.assertEqual(missing.status_code, 404)

    def test_create_case_records_context_and_serves_original(self) -> None:
        case = self.create_case(
            question="Which sector moved most?",
            preserve="Keep title, values, and dimensions unchanged",
            max_tokens=500000,
        )

        self.assertEqual(case["state"], "critique")
        self.assertEqual(case["context_version"], 1)
        self.assertEqual(case["context"]["fields"]["audience"]["value"], "Board members")
        self.assertEqual(case["context"]["fields"]["question"]["source"], "user")
        self.assertEqual(case["limits"]["max_tokens"], 500000)
        self.assertEqual(case["request_checks"][0]["kind"], "preserve")
        self.assertIn("dimensions", case["request_checks"][0]["acceptance_check"]["required"])
        artifact = self.client.get(case["artifact_urls"]["original"])
        self.assertEqual(artifact.status_code, 200)
        self.assertEqual(artifact.content, PNG_1X1)

    def test_context_update_and_feedback_remain_structured(self) -> None:
        case = self.create_case()
        case_id = case["case_id"]

        updated = self.client.post(
            f"/api/cases/{case_id}/context",
            json={
                "text": "This will be read on a phone.",
                "medium": "Mobile web",
                "source": "user",
            },
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["context_version"], 2)
        self.assertEqual(updated.json()["context"]["fields"]["medium"]["value"], "Mobile web")

        feedback = self.client.post(
            f"/api/cases/{case_id}/feedback",
            json={
                "text": "Move each label closer to its mark.",
                "target": "Category to mark binding",
                "current": "Labels require long horizontal tracing",
                "required": "Each label and mark read as one unit",
                "why": "Reduce identity lookup effort",
            },
        )
        self.assertEqual(feedback.status_code, 200, feedback.text)
        check = feedback.json()["feedback"][-1]["acceptance_check"]
        self.assertEqual(check["target"], "Category to mark binding")
        self.assertIn("one unit", check["required"])

    def test_intake_check_api_records_change_contract_before_iteration(self) -> None:
        case = self.create_case()
        response = self.client.post(
            f"/api/cases/{case['case_id']}/checks",
            json={
                "kind": "change",
                "text": "Remove the top legend.",
                "target": "Top legend",
                "current": "Legend remains above the plot",
                "required": "Top legend is absent",
                "why": "The labels move into the chart",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        check = response.json()["request_checks"][-1]
        self.assertEqual(check["kind"], "change")
        self.assertEqual(check["acceptance_check"]["target"], "Top legend")

    def test_manual_candidate_stop_and_resume_follow_state_machine(self) -> None:
        case = self.create_case()
        case_id = case["case_id"]
        case = self.record_semantic_preflight(case_id)
        self.assertEqual(case["semantic_preflights"][0]["context_version"], 1)
        candidate = self.client.post(
            f"/api/cases/{case_id}/iterations",
            data={"summary": "First repair"},
            files={"chart": ("candidate.png", PNG_1X1 + b"candidate", "image/png")},
        )
        self.assertEqual(candidate.status_code, 200, candidate.text)
        self.assertEqual(candidate.json()["state"], "blind_review")
        self.assertEqual(candidate.json()["iterations"][0]["context_version"], 1)
        self.assertIsNotNone(candidate.json()["artifact_urls"]["latest"])

        stopped = self.client.post(
            f"/api/cases/{case_id}/stop",
            json={"kind": "user_stop", "reason": "Pause for a context check"},
        )
        self.assertEqual(stopped.status_code, 200, stopped.text)
        self.assertEqual(stopped.json()["state"], "stopped")

        resumed = self.client.post(
            f"/api/cases/{case_id}/resume",
            json={"reason": "Context confirmed", "to": "revise"},
        )
        self.assertEqual(resumed.status_code, 200, resumed.text)
        self.assertEqual(resumed.json()["state"], "revise")

    def test_rejects_fake_images_bad_ids_and_invalid_budgets(self) -> None:
        fake = self.client.post(
            "/api/cases",
            data={"max_iterations": "3"},
            files={"chart": ("chart.png", b"not a png", "image/png")},
        )
        self.assertEqual(fake.status_code, 400)
        incoming = self.root / "incoming"
        self.assertFalse(any(path.is_file() for path in incoming.rglob("*") if incoming.exists()))

        invalid_budget = self.client.post(
            "/api/cases",
            data={"max_iterations": "0"},
            files={"chart": ("chart.png", PNG_1X1, "image/png")},
        )
        self.assertEqual(invalid_budget.status_code, 422)

        traversal = self.client.get("/api/cases/%2E%2E%2Foutside")
        self.assertIn(traversal.status_code, (404, 409))


if __name__ == "__main__":
    unittest.main()
