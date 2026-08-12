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

        self.assertEqual(case["state"], "build")
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
