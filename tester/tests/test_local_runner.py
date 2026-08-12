from __future__ import annotations

import tempfile
import time
import unittest
import re
import os
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from PIL import Image

from tester.local_runner import LocalCodexRunner, safe_environment


class FakeCaseManager:
    def __init__(self, root: Path):
        self.root = root
        self.case_id = "case-1"
        self.case_dir = root / "cases" / self.case_id
        self.case_dir.mkdir(parents=True)
        original = self.case_dir / "original.png"
        original.write_bytes(b"original")
        self.data = {
            "case_id": self.case_id,
            "state": "build",
            "original": {"path": str(original)},
            "iterations": [],
            "evaluations": [],
            "limits": {"max_tokens": None},
            "telemetry": {"total_tokens": 0},
            "budget_status": {"exhausted": []},
        }
        self.calls: list[tuple[object, ...]] = []

    def status(self, case_id: str) -> dict:
        if case_id != self.case_id:
            raise RuntimeError("missing case")
        return self.data

    def run(self, *args: object) -> dict:
        self.calls.append(args)
        if args[0] == "build-check":
            return {}
        if args[0] == "iterate":
            artifact = Path(str(args[args.index("--output") + 1]))
            self.data["iterations"].append(
                {"number": 1, "artifact": {"path": str(artifact)}}
            )
            self.data["state"] = "blind_review"
            return {}
        if args[0] == "review-request":
            request = self.case_dir / "review-blind-request-01.json"
            request.write_text("{}", encoding="utf-8")
            return {"request": str(request)}
        if args[0] == "evaluate":
            self.data["evaluations"].append({"iteration": 1, "verdict": "Revise"})
            self.data["state"] = "revise"
            return {}
        if args[0] in ("usage", "stop"):
            return {}
        raise AssertionError(f"Unexpected case-manager call: {args}")


class LocalRunnerTests(unittest.TestCase):
    def test_provider_keys_are_not_passed_to_chart_subprocesses(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PATH": "/usr/bin",
                "HOME": "/tmp/home",
                "OPENAI_API_KEY": "openai-secret",
                "ANTHROPIC_API_KEY": "anthropic-secret",
                "GOOGLE_API_KEY": "google-secret",
            },
            clear=True,
        ):
            env = safe_environment({"DATAVIZ_FIX_ROOT": "/tmp/cases"})
        self.assertEqual(env["PATH"], "/usr/bin")
        self.assertEqual(env["DATAVIZ_FIX_ROOT"], "/tmp/cases")
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("GOOGLE_API_KEY", env)

    def test_one_job_runs_one_creator_and_one_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            stages: list[str] = []

            def fake_invoke(job_id, stage, prompt, images, case_dir):
                stages.append(stage)
                self.assertIn(client.case_id, prompt)
                self.assertEqual(case_dir, client.case_dir)
                if stage == "creator":
                    match = re.search(r"Render exactly one real PNG to (.+?) and inspect", prompt)
                    self.assertIsNotNone(match)
                    artifact = Path(match.group(1))
                    artifact.write_bytes(b"candidate")
                else:
                    self.assertEqual(len(images), 2)
                    (client.case_dir / "review-response-01.json").write_text("{}", encoding="utf-8")
                    client.data["state"] = "context_reveal"
                return {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "cached_input_tokens": 2,
                    "latency_seconds": 0.1,
                }

            runner._invoke = fake_invoke  # type: ignore[method-assign]
            job = runner.start(client.case_id)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                job = runner.get(job["job_id"])
                if job["status"] in ("complete", "failed"):
                    break
                time.sleep(0.01)

            self.assertEqual(job["status"], "complete", job)
            self.assertEqual(stages, ["creator", "reviewer"])
            self.assertEqual(client.data["state"], "revise")
            self.assertEqual(
                [call[0] for call in client.calls],
                ["build-check", "usage", "iterate", "review-request", "usage", "evaluate"],
            )

    def test_usage_parser_uses_completed_turn(self) -> None:
        output = "\n".join(
            (
                '{"type":"item.completed"}',
                '{"type":"turn.completed","usage":{"input_tokens":120,"cached_input_tokens":40,"output_tokens":30}}',
            )
        )
        self.assertEqual(
            LocalCodexRunner._parse_usage(output),
            {"input_tokens": 120, "cached_input_tokens": 40, "output_tokens": 30},
        )

    def test_measured_cycle_estimate_blocks_an_underfunded_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            (client.case_dir / "case.json").write_text(
                '{"telemetry":{"events":['
                '{"iteration":1,"stage":"creator","total_tokens":400},'
                '{"iteration":1,"stage":"reviewer","total_tokens":300}'
                ']}}',
                encoding="utf-8",
            )
            client.data["limits"]["max_tokens"] = 600
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            self.assertEqual(runner.estimated_cycle_tokens(), 700)
            with self.assertRaisesRegex(ValueError, "only 600 remain"):
                runner.start(client.case_id)

    def test_prompt_is_sent_through_stdin_not_after_image_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            runner.executable = "/usr/bin/true"
            runner.jobs["job"] = {
                "job_id": "job",
                "case_id": client.case_id,
                "stage": "creator",
                "updated_at": "",
                "events": [],
            }
            with patch("tester.local_runner.subprocess.run") as run:
                run.return_value = CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout='{"type":"turn.completed","usage":{}}\n',
                    stderr="",
                )
                runner._invoke(
                    "job",
                    "creator",
                    "the prompt",
                    [Path(client.data["original"]["path"])],
                    client.case_dir,
                )
            command = run.call_args.args[0]
            kwargs = run.call_args.kwargs
            self.assertEqual(command[-1], "-")
            self.assertNotIn("the prompt", command)
            self.assertEqual(kwargs["input"], "the prompt")
            self.assertEqual(kwargs["env"]["MPLCONFIGDIR"], str(client.case_dir / ".matplotlib"))
            self.assertEqual(kwargs["env"]["XDG_CACHE_HOME"], str(client.case_dir / ".cache"))

    def test_reasoning_effort_can_be_overridden_for_fast_local_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ,
            {"DATAVIZ_CODEX_REASONING_EFFORT": "medium"},
        ):
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            runner.executable = "/usr/bin/true"
            runner.jobs["job"] = {
                "job_id": "job",
                "case_id": client.case_id,
                "stage": "creator",
                "updated_at": "",
                "events": [],
            }
            with patch("tester.local_runner.subprocess.run") as run:
                run.return_value = CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout='{"type":"turn.completed","usage":{}}\n',
                    stderr="",
                )
                runner._invoke(
                    "job",
                    "creator",
                    "the prompt",
                    [Path(client.data["original"]["path"])],
                    client.case_dir,
                )
            command = run.call_args.args[0]
            self.assertIn('model_reasoning_effort="medium"', command)

    def test_reviewer_prompt_preserves_frozen_blind_reads_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            prompt = runner._reviewer_prompt(
                client.case_id,
                client.case_dir / "review-blind-request-01.json",
                client.case_dir,
                1,
            )
            self.assertIn("byte-for-byte", prompt)
            self.assertIn("Do not shorten, paraphrase, correct", prompt)

    def test_revision_uses_latest_candidate_and_preserves_prior_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            latest = client.case_dir / "iteration-01.png"
            latest.write_bytes(b"latest")
            client.data["iterations"].append(
                {"number": 1, "artifact": {"path": str(latest)}}
            )
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            images = runner._creator_images(client.data)
            prompt = runner._creator_prompt(
                client.case_id,
                client.case_dir,
                client.case_dir / "candidate-02.png",
                2,
            )
            self.assertEqual(images, [Path(client.data["original"]["path"]), latest])
            self.assertIn("Continue from the latest candidate", prompt)
            self.assertIn("Preserve what already passes", prompt)
            self.assertIn("unless the latest verdict is Redesign", prompt)

    def test_reviewer_gets_delivery_preview_and_overlapping_detail_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            artifact = client.case_dir / "candidate.png"
            Image.new("RGB", (1600, 1000), "white").save(artifact)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            images = runner._reviewer_images(
                Path(client.data["original"]["path"]), artifact, client.case_dir, 1
            )
            self.assertEqual(len(images), 4)
            self.assertTrue(images[2].is_file())
            self.assertTrue(images[3].is_file())
            with Image.open(images[2]) as preview:
                self.assertLessEqual(max(preview.size), 1200)
            with Image.open(images[3]) as details:
                self.assertGreater(details.width, details.height)


if __name__ == "__main__":
    unittest.main()
