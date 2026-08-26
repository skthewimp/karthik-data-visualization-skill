from __future__ import annotations

import tempfile
import time
import unittest
import re
import os
import base64
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from PIL import Image

from tester.local_runner import LocalCodexRunner, safe_environment


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class FakeCaseManager:
    def __init__(self, root: Path):
        self.root = root
        self.case_id = "case-1"
        self.case_dir = root / "cases" / self.case_id
        self.case_dir.mkdir(parents=True)
        original = self.case_dir / "original.png"
        original.write_bytes(PNG_1X1)
        self.data = {
            "case_id": self.case_id,
            "state": "build",
            "context_version": 1,
            "original": {"path": str(original)},
            "iterations": [],
            "semantic_preflights": [],
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
        if args[0] == "inspect":
            report = Path(str(args[args.index("--report") + 1]))
            self.data["iterations"][-1]["inspection"] = {
                "path": str(report),
                "sha256": "inspection-sha",
            }
            return {}
        if args[0] == "evaluate":
            self.data["evaluations"].append({"iteration": 1, "verdict": "Revise"})
            self.data["state"] = "revise"
            return {}
        if args[0] in ("usage", "stop"):
            return {}
        raise AssertionError(f"Unexpected case-manager call: {args}")


class LocalRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.codex_home = tempfile.TemporaryDirectory()
        writing_skill = (
            Path(cls.codex_home.name)
            / "skills"
            / "karthik-writing-style"
            / "SKILL.md"
        )
        writing_skill.parent.mkdir(parents=True)
        writing_skill.write_text("# Test writing skill\n", encoding="utf-8")
        cls.codex_home_patch = patch.dict(
            os.environ, {"CODEX_HOME": cls.codex_home.name}
        )
        cls.codex_home_patch.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.codex_home_patch.stop()
        cls.codex_home.cleanup()

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

    def test_missing_required_skill_stops_the_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, root, enabled=True)
            with self.assertRaisesRegex(RuntimeError, "Required installed skill not found"):
                runner._skill_path("missing-style-skill")

    def test_one_job_runs_staged_creator_then_one_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            stages: list[str] = []

            def fake_invoke(job_id, stage, prompt, images, case_dir):
                stages.append(stage)
                self.assertIn(client.case_id, prompt)
                self.assertEqual(case_dir, client.case_dir)
                if stage == "diagnose":
                    (client.case_dir / "diagnose-01.md").write_text(
                        "## APPARENT QUESTION\nWhat changed?\n", encoding="utf-8"
                    )
                elif stage == "select":
                    # No image on the cold-selection call.
                    self.assertEqual(images, [])
                    # Structured-text handoff: markdown sections plus a routing block.
                    (client.case_dir / "select-01.md").write_text(
                        "## DESIGN\nDirect-labelled lines.\n\n"
                        "```routing\nbuilder: chart\nneeds_annotations: no\n"
                        "needs_explainer: no\nneeds_color_plan: no\n"
                        "needs_precision_plan: no\n```\n",
                        encoding="utf-8",
                    )
                elif stage == "build":
                    match = re.search(r"Render exactly one real PNG to (.+?) and inspect", prompt)
                    self.assertIsNotNone(match)
                    Path(match.group(1)).write_bytes(PNG_1X1)
                    client.data["semantic_preflights"].append({"context_version": 1})
                else:
                    self.assertEqual(stage, "reviewer")
                    self.assertEqual(len(images), 4)
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
            self.assertEqual(stages, ["diagnose", "select", "build", "reviewer"])
            self.assertEqual(client.data["state"], "revise")
            self.assertEqual(
                [call[0] for call in client.calls],
                [
                    "usage",
                    "usage",
                    "usage",
                    "build-check",
                    "iterate",
                    "inspect",
                    "review-request",
                    "usage",
                    "evaluate",
                ],
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
            self.assertEqual(kwargs["env"]["PYTHONPATH"], str(runner.repo_root))
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
            self.assertIn("active user checks as the change contract", prompt)
            self.assertIn("every applicable panel, facet, row, or series", prompt)
            self.assertIn("baseline_concerns", prompt)
            self.assertIn("After the blind response is frozen", prompt)
            self.assertIn("karthik-data-visualization", prompt)
            self.assertIn("karthik-writing-style", prompt)
            self.assertIn("closest competing encoded colours", prompt)
            self.assertLess(
                prompt.index("blind response is frozen"),
                prompt.index("karthik-writing-style"),
            )

    def test_build_prompt_loads_builder_and_writing_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            prompt = runner._build_prompt(
                client.case_id,
                client.case_dir,
                client.case_dir / "candidate-01.png",
                client.case_dir / "diagnose-01.json",
                client.case_dir / "select-01.json",
                1,
                1,
                "chart",
                (),
            )
            self.assertIn("karthik-data-visualization/codex/SKILL.md", prompt)
            self.assertIn("karthik-writing-style", prompt)
            self.assertIn("required inputs, not optional references", prompt)
            self.assertIn("closest pair of competing encoded colours", prompt)
            # The build call must NOT drag in the diagnosis or selection skills - that is the
            # whole point of staging: no single call holds every skill.
            self.assertNotIn("dataviz-selector/codex/SKILL.md", prompt)
            self.assertNotIn("dataviz-brief/codex/SKILL.md", prompt)

    def test_build_prompt_swaps_to_table_builder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            prompt = runner._build_prompt(
                client.case_id,
                client.case_dir,
                client.case_dir / "candidate-01.png",
                client.case_dir / "diagnose-01.json",
                client.case_dir / "select-01.json",
                1,
                1,
                "table",
                (),
            )
            self.assertIn("karthik-table-style/codex/SKILL.md", prompt)
            self.assertNotIn("karthik-data-visualization/codex/SKILL.md", prompt)

    def test_diagnose_prompt_is_scoped_to_its_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeCaseManager(root)
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            prompt = runner._diagnose_prompt(
                client.case_id, client.case_dir, client.case_dir / "diagnose-01.json", 1
            )
            self.assertIn("dataviz-brief/codex/SKILL.md", prompt)
            self.assertIn("dataviz-extract/codex/SKILL.md", prompt)
            self.assertIn("dataviz-critique/codex/SKILL.md", prompt)
            # Diagnose does not choose a form or build, so its build skills must be absent.
            self.assertNotIn("dataviz-selector/codex/SKILL.md", prompt)
            self.assertNotIn("karthik-data-visualization/codex/SKILL.md", prompt)
            self.assertIn("do not render", prompt.lower())

    def test_revision_build_uses_latest_candidate_and_preserves_prior_passes(self) -> None:
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
            prompt = runner._build_prompt(
                client.case_id,
                client.case_dir,
                client.case_dir / "candidate-02.png",
                client.case_dir / "diagnose-02.json",
                client.case_dir / "select-02.json",
                2,
                1,
                "chart",
                (),
            )
            self.assertEqual(images, [Path(client.data["original"]["path"]), latest])
            self.assertIn("Continue from the latest candidate", prompt)
            self.assertIn("Preserve what already passes", prompt)
            self.assertIn("unless the latest verdict is Redesign", prompt)
            self.assertIn("edit boundary", prompt)
            self.assertIn("do not retain or restore a forbidden element", prompt)
            self.assertIn("every applicable panel, facet, row, or series", prompt)
            self.assertIn("semantic-preflight", prompt)
            self.assertIn("structured field marked `inferred`", prompt)

    def test_read_builder_choice_parses_routing_block_and_wires_all_conditionals(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            select = Path(temp) / "select-01.md"
            select.write_text(
                "## DESIGN\nGrouped bars.\n\n"
                "```routing\nbuilder: table\nneeds_annotations: yes\n"
                "needs_explainer: no\nneeds_color_plan: yes\n"
                "needs_precision_plan: yes\n```\n",
                encoding="utf-8",
            )
            builder, active = LocalCodexRunner._read_builder_choice(select)
            self.assertEqual(builder, "table")
            # The colour and precision conditional skills must now be wired - the pre-existing
            # gap where only annotations/explainer were activated is fixed.
            self.assertEqual(
                set(active), {"chart-annotations", "dataviz-color", "dataviz-precision"}
            )

    def test_read_builder_choice_defaults_when_artifact_is_garbled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            select = Path(temp) / "select-01.md"
            select.write_text("## DESIGN\nno routing block here at all\n", encoding="utf-8")
            builder, active = LocalCodexRunner._read_builder_choice(select)
            self.assertEqual(builder, "chart")
            self.assertEqual(active, ())

    def test_select_prompt_requests_routing_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            client = FakeCaseManager(Path(temp))
            runner = LocalCodexRunner(client, Path(__file__).resolve().parents[2], enabled=True)
            prompt = runner._select_prompt(
                client.case_id,
                client.case_dir,
                client.case_dir / "diagnose-01.md",
                client.case_dir / "select-01.md",
                1,
            )
            self.assertIn("```routing", prompt)
            self.assertIn("needs_color_plan", prompt)
            self.assertIn("needs_precision_plan", prompt)
            self.assertNotIn("as JSON", prompt)

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
