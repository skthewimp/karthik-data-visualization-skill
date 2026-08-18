from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from public_site.app import create_app
from public_site.runner import now_iso, read_case, write_case


def chart_png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (640, 400), "white").save(output, format="PNG")
    return output.getvalue()


class ImmediateRunner:
    model = "gpt-5.6-luna"

    def public_config(self) -> dict[str, object]:
        return {"provider_runner": True, "model": self.model}

    def start(self, case_dir: Path, safety_identifier: str) -> dict[str, object]:
        data = read_case(case_dir)
        number = len(data["iterations"]) + 1
        artifact = case_dir / f"repaired-{number}.png"
        artifact.write_bytes((case_dir / data["original"]).read_bytes())
        data["iterations"].append(
            {
                "number": number,
                "artifact": artifact.name,
                "review": {
                    "verdict": "Send",
                    "summary": "The repair is ready.",
                    "required_changes": [],
                },
                "created_at": now_iso(),
            }
        )
        data["pending_feedback"] = None
        data["status"] = "ready"
        write_case(case_dir, data)
        return {"job_id": uuid4().hex, "status": "complete"}


class PublicSiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "runtime"
        self.runner = ImmediateRunner()
        self.client = TestClient(
            create_app(self.root, runner=self.runner, secure_cookie=False)
        )

    def tearDown(self) -> None:
        self.client.close()
        self.temp.cleanup()

    def create_case(self, prompt: str = "Make the comparison clearer") -> dict:
        response = self.client.post(
            "/api/cases",
            data={"prompt": prompt},
            files={"chart": ("chart.png", chart_png(), "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_landing_page_and_health_are_public(self) -> None:
        landing = self.client.get("/")
        self.assertEqual(landing.status_code, 200)
        self.assertIn("Upload a chart", landing.text)
        health = self.client.get("/healthz")
        self.assertEqual(health.json()["model"], "gpt-5.6-luna")

    def test_image_and_prompt_create_side_by_side_result(self) -> None:
        case = self.create_case()
        self.assertEqual(case["status"], "ready")
        self.assertTrue(case["can_retry"])
        self.assertIn("approximate", case["values_note"])
        self.assertEqual(self.client.get(case["original_url"]).status_code, 200)
        self.assertEqual(self.client.get(case["repaired_url"]).status_code, 200)
        download = self.client.get(case["download_url"])
        self.assertEqual(download.status_code, 200)
        self.assertIn("repaired-chart.png", download.headers["content-disposition"])

    def test_one_retry_is_allowed_and_second_is_rejected(self) -> None:
        case = self.create_case()
        first = self.client.post(
            f"/api/cases/{case['case_id']}/retry",
            data={"feedback": "Move the labels closer to the bars"},
        )
        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json()["can_retry"])
        second = self.client.post(
            f"/api/cases/{case['case_id']}/retry",
            data={"feedback": "Try a third version"},
        )
        self.assertEqual(second.status_code, 409)

    def test_case_is_bound_to_the_browser_cookie(self) -> None:
        case = self.create_case()
        stranger = TestClient(create_app(self.root, runner=self.runner, secure_cookie=False))
        try:
            response = stranger.get(f"/api/cases/{case['case_id']}")
            self.assertEqual(response.status_code, 404)
        finally:
            stranger.close()

    def test_invalid_upload_and_prompt_are_rejected(self) -> None:
        tiny = io.BytesIO()
        Image.new("RGB", (10, 10), "white").save(tiny, format="PNG")
        response = self.client.post(
            "/api/cases",
            data={"prompt": "Repair it"},
            files={"chart": ("tiny.png", tiny.getvalue(), "image/png")},
        )
        self.assertEqual(response.status_code, 400)

        fake = self.client.post(
            "/api/cases",
            data={"prompt": "Repair it"},
            files={"chart": ("chart.png", b"not an image", "image/png")},
        )
        self.assertEqual(fake.status_code, 400)


if __name__ == "__main__":
    unittest.main()
