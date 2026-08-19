import json
import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from dataviz_mcp.comparison import compare_chart_artifacts
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.rendering import render_chart


SCRIPT = Path(__file__).resolve().parents[1] / "codex" / "scripts" / "case_manager.py"
FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "dataviz_mcp"
    / "tests"
    / "fixtures"
    / "chart_fixtures.py"
)
CORE_GATES = {"Evidence", "Visual reasoning", "Information fit", "Delivery"}
GATES = (
    "Evidence",
    "Question",
    "Insight",
    "Visual reasoning",
    "Information fit",
    "Delivery",
)
RELEASE_CHECKS = (
    "Visual integrity",
    "Relationship traceability",
    "Spatial economy",
    "Encoding semantics",
    "Delivery robustness",
)
PRESENTATION_CHECKS = (
    "Colour distinction",
    "Copy style",
)
SEMANTIC_DIMENSIONS = (
    "measure",
    "time_context",
    "universe_denominator",
    "claim_strength",
    "audience_units",
)


class CaseManagerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env["DATAVIZ_FIX_ROOT"] = str(self.root / "runtime")
        self.original = self.write_png("original.png", b"original")

    def tearDown(self):
        self.temp.cleanup()

    def write_png(self, name, payload):
        path = self.root / name
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + payload)
        return path

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            ["python3", str(SCRIPT), *map(str, args)],
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )
        if ok and result.returncode != 0:
            self.fail(f"command failed: {' '.join(map(str, args))}\n{result.stderr}")
        if not ok and result.returncode == 0:
            self.fail(f"command unexpectedly passed: {' '.join(map(str, args))}")
        return result

    def start(self, *extra):
        output = self.run_cli(
            "start",
            "--session",
            "test-session",
            "--image",
            self.original,
            "--creator",
            "creator-agent",
            *extra,
        )
        started = json.loads(output.stdout)
        self.record_semantic_preflight()
        return started

    def record_semantic_preflight(self, result="clear"):
        status = self.status()
        if status["state"] in ("critique", "redesign"):
            critique_report = self.root / f"critique-v{status['context_version']}.json"
            critique_report.write_text(
                json.dumps(
                    {
                        "context_version": status["context_version"],
                        "apparent_question": "What comparison does the source chart support?",
                        "apparent_claim": "The visible comparison is the apparent claim.",
                        "evidence_limitations": ["Only source-fidelity evidence is available"],
                        "source_inventory": {
                            "structure": ["One source chart"],
                            "required_content": ["Visible periods, categories, labels, and units"],
                            "semantic_mappings": ["Existing label-to-mark mappings"],
                            "uncertainties": [],
                        },
                        "layout_risks": ["Long labels and neighbouring zones at delivery size"],
                        "findings": {
                            "fatal": [],
                            "major": [
                                {
                                    "id": "c1",
                                    "problem": "The requested repair must remain explicit",
                                    "reader_consequence": "The requested comparison could remain unclear",
                                    "observable_condition": "The repaired chart makes the comparison explicit",
                                }
                            ],
                            "minor": [],
                        },
                        "highest_consequence_findings": ["c1"],
                        "misleading_reader_interpretation": "The source can be read as an unsupported claim",
                        "defensible_interpretation": "Only the visible comparison is supported",
                        "intervention": "repair",
                        "form_questioned": False,
                        "required_delivered_outcomes": ["The requested comparison is explicit"],
                        "preserve": [],
                    }
                ),
                encoding="utf-8",
            )
            self.run_cli("critique", "--session", "test-session", "--report", critique_report)
            status = self.status()
            critique_number = status["critiques"][-1]["number"]
            design_report = self.root / f"design-v{status['context_version']}.json"
            design_report.write_text(
                json.dumps(
                    {
                        "critique_number": critique_number,
                        "requirements": [
                            {
                                "finding_id": "c1",
                                "planned_change": "Make the requested comparison explicit",
                                "affected_zones": ["plot"],
                                "observable_outcome": "The comparison is directly readable",
                            }
                        ],
                        "measure_scope": "Source-fidelity measure",
                        "evidence_scope": "Source chart only",
                        "chart_form": "Existing chart form",
                        "primary_identification": "Existing labels",
                        "zones": {
                            "title": "Claim",
                            "subtitle": "Scope",
                            "legend": "Identity only when needed",
                            "plot": "Primary comparison",
                            "annotation": "Evidence-bounded context",
                            "footer": "Source and caveat",
                        },
                        "colour_role": "Identity or emphasis only",
                        "selector_decision": None,
                        "preservation_plan": [
                            {
                                "source_item": "Visible periods, categories, labels, and units",
                                "planned_treatment": "Carry all legible source content into the repair",
                                "observable_outcome": "Every legible source item remains identifiable",
                            },
                            {
                                "source_item": "Existing label-to-mark mappings",
                                "planned_treatment": "Preserve each identity while changing the presentation",
                                "observable_outcome": "Each label still identifies the correct mark",
                            },
                        ],
                        "layout_plan": {
                            "delivery_size": "1200 by 675 pixels",
                            "longest_text": "Measure the longest visible label before plotting",
                            "dense_regions": "Inspect title, plot edges, and footer",
                            "collision_risks": ["Long labels could collide with marks or margins"],
                            "mitigation": "Reserve label and footer space before plotting",
                            "preview_check": "Inspect the complete 1200 by 675 export",
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
                ),
                encoding="utf-8",
            )
            self.run_cli("design-contract", "--session", "test-session", "--report", design_report)
            renderer_report = self.root / f"renderer-v{status['context_version']}.json"
            renderer_report.write_text(
                json.dumps(
                    {
                        "requested": "matplotlib",
                        "selected": "matplotlib",
                        "ggplot2_supported": True,
                        "reason": "Explicit test renderer",
                        "probe": {
                            "renderers": {
                                "ggplot2": {"available": True, "failure_reasons": []},
                                "matplotlib": {"available": True},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.run_cli("renderer-selection", "--session", "test-session", "--report", renderer_report)
            status = self.status()
        report = self.root / f"semantic-preflight-v{status['context_version']}.json"
        report.write_text(
            json.dumps(
                {
                    "context_version": status["context_version"],
                    "dimensions": {
                        name: {
                            "result": result,
                            "observed": f"Observed {name}",
                            "risk": f"Risk assessed for {name}",
                            "required": f"Required delivered state for {name}",
                        }
                        for name in SEMANTIC_DIMENSIONS
                    },
                }
            ),
            encoding="utf-8",
        )
        output = self.run_cli(
            "semantic-preflight",
            "--session",
            "test-session",
            "--report",
            report,
        )
        return json.loads(output.stdout)

    @staticmethod
    def blind_semantics():
        return {
            name: {
                "reading": f"Blind visible reading for {name}",
                "uncertainty": f"Blind uncertainty for {name}",
            }
            for name in SEMANTIC_DIMENSIONS
        }

    def status(self):
        output = self.run_cli("status", "--session", "test-session")
        return json.loads(output.stdout)

    def ensure_revision_contract(self):
        status = self.status()
        if status["state"] == "revise":
            latest = status["iterations"][-1]
            open_actions = status["evaluations"][-1].get("open_required_actions", []) if status["evaluations"] else []
            superseded_actions = {
                action_id
                for item in status["feedback"]
                for action_id in item.get("supersedes_actions", [])
            }
            open_actions = [item for item in open_actions if item["id"] not in superseded_actions]
            built_feedback = latest.get("feedback_count", 0)
            new_feedback = [
                {"id": f"f{item['number']}"}
                for item in status["feedback"][built_feedback:]
                if not item.get("superseded_by_feedback")
            ]
            changes = [
                {
                    "source_id": item["id"],
                    "planned_change": "Apply the complete requested correction",
                    "affected_zones": ["plot"],
                    "observable_outcome": "The named action passes direct inspection",
                }
                for item in open_actions + new_feedback
            ]
            revision = self.root / f"revision-{latest['number']}.json"
            revision.write_text(json.dumps({"changes": changes}), encoding="utf-8")
            self.run_cli("revision-contract", "--session", "test-session", "--report", revision)

    def iterate(self, path, summary="candidate"):
        self.ensure_revision_contract()
        output = self.run_cli(
            "iterate",
            "--session",
            "test-session",
            "--output",
            path,
            "--summary",
            summary,
        )
        return json.loads(output.stdout)

    def ensure_inspection(self):
        current = self.status()
        iteration = current["iterations"][-1]
        if iteration.get("inspection"):
            return
        inspection = self.root / f"inspection-{iteration['number']}.json"
        inspection.write_text(
            json.dumps(
                {
                    "artifact": iteration["artifact"],
                    "layout_metadata": None,
                    "checks_complete": False,
                    "passes_geometry_checks": False,
                    "defects": [],
                    "review_views": [],
                }
            ),
            encoding="utf-8",
        )
        self.run_cli("inspect", "--session", "test-session", "--report", inspection)

    def review(
        self,
        verdict="Revise",
        carry_forward_result="Pass",
        acceptance_result="Pass",
        insight_result=None,
        omit_release_stress_test=False,
        inspection_sha_override=None,
        semantic_result="Pass",
        presentation_result="Pass",
        omit_presentation_check=None,
        omit_presentation_section=False,
        tamper_blind_semantics=False,
        action_override=None,
        ok=True,
    ):
        self.ensure_inspection()
        request_output = self.run_cli("review-request", "--session", "test-session")
        request = json.loads(request_output.stdout)
        status = self.status()
        iteration = status["iterations"][-1]
        blind = {
            "reviewer": "reviewer-agent",
            "iteration": iteration["number"],
            "artifact_sha256": iteration["artifact"]["sha256"],
            "context_version": iteration.get("context_version", 1),
            "expert": "Blind expert read",
            "audience": "Blind audience read",
            "semantics": self.blind_semantics(),
        }
        Path(request["blind_response"]).write_text(json.dumps(blind), encoding="utf-8")
        reveal_output = self.run_cli("blind-submit", "--session", "test-session")
        reveal_meta = json.loads(reveal_output.stdout)
        reveal = json.loads(Path(reveal_meta["reveal"]).read_text(encoding="utf-8"))

        gates = {}
        for name in GATES:
            required = name in CORE_GATES
            result = "Pass" if required else "Unknown"
            gates[name] = {"required": required, "result": result, "evidence": f"Evidence for {name}"}
        if insight_result is not None:
            gates["Insight"]["required"] = True
            gates["Insight"]["result"] = insight_result
        release_checks = {
            name: {
                "result": "Pass",
                "evidence": f"Evidence for {name}",
                "stress_test": f"Worst-case region for {name}",
            }
            for name in RELEASE_CHECKS
        }
        semantic_checks = {
            name: {
                "result": semantic_result,
                "misleading_interpretation": f"Competing reading for {name}",
                "defensible_interpretation": f"Supported reading for {name}",
                "evidence": f"Direct semantic evidence for {name}",
            }
            for name in SEMANTIC_DIMENSIONS
        }
        presentation_checks = {
            name: {
                "result": presentation_result,
                "evidence": f"Evidence for {name}",
                "stress_test": f"Worst-case copy or colour pair for {name}",
            }
            for name in PRESENTATION_CHECKS
            if name != omit_presentation_check
        }
        if omit_release_stress_test:
            release_checks["Visual integrity"].pop("stress_test")
        codes = []
        actions = []
        if verdict in ("Revise", "Redesign"):
            gates["Visual reasoning"]["result"] = "Concern"
            release_checks["Spatial economy"]["result"] = "Concern"
            codes = ["R3"]
            actions = [
                {
                    "target": "Chart geometry",
                    "from": "The current spacing does not pass",
                    "to": "All named zones pass at delivery size",
                    "why": "Readers need immediate traceability",
                    "codes": ["R3"],
                    "affected_zones": ["plot"],
                }
            ]
            if action_override is not None:
                actions = action_override
        elif verdict == "Not evaluable":
            gates["Evidence"]["result"] = "Unknown"
            codes = ["D2"]
            actions = ["Supply the missing evidence"]

        report = {
            "reviewer": blind["reviewer"],
            "reviewer_role": "independent",
            "review_token": reveal["review_token"],
            "blind_response_sha256": reveal["blind_response_sha256"],
            "iteration": iteration["number"],
            "artifact_sha256": iteration["artifact"]["sha256"],
            "deterministic_inspection_sha256": (
                inspection_sha_override
                if inspection_sha_override is not None
                else iteration.get("inspection", {}).get("sha256")
            ),
            "context_version": iteration.get("context_version", 1),
            "scope": "Source fidelity at screen size",
            "tested_size": "1200 px wide",
            "blind_reads": {"expert": blind["expert"], "audience": blind["audience"]},
            "blind_semantics": blind["semantics"],
            "gates": gates,
            "semantic_checks": semantic_checks,
            "release_checks": release_checks,
            "carry_forward_checks": [
                {
                    "id": item["id"],
                    "result": carry_forward_result,
                    "evidence": f"Direct recheck of {item['id']}",
                }
                for item in reveal.get("carry_forward_required_actions", [])
            ],
            "acceptance_checks": [
                {
                    "id": item["id"],
                    "result": acceptance_result,
                    "evidence": f"Direct recheck of {item['id']}",
                }
                for item in reveal.get("active_acceptance_checks", [])
            ],
            "critique_checks": [
                {
                    "id": item["id"],
                    "result": "Pass",
                    "evidence": f"Direct closure evidence for {item['id']}",
                }
                for severity in ("fatal", "major")
                for item in reveal.get("critique_contract", {}).get("findings", {}).get(severity, [])
            ],
            "verdict": verdict,
            "codes": codes,
            "required_actions": actions,
        }
        if not omit_presentation_section:
            report["presentation_checks"] = presentation_checks
        if tamper_blind_semantics:
            report["blind_semantics"]["measure"]["reading"] = "Rewritten after reveal"
        response_path = Path(reveal["response_path"])
        response_path.write_text(json.dumps(report), encoding="utf-8")
        output = self.run_cli(
            "evaluate",
            "--session",
            "test-session",
            "--report",
            response_path,
            ok=ok,
        )
        return json.loads(output.stdout) if ok else output

    def test_render_bundle_and_inspection_are_bound_to_exact_iteration(self):
        self.start()
        candidate = self.write_png("candidate.png", b"candidate")
        artifact_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
        spec = self.root / "chart-spec.json"
        layout = self.root / "layout-metadata.json"
        spec.write_text('{"renderer":"matplotlib"}', encoding="utf-8")
        layout.write_text(
            json.dumps(
                {
                    "coordinate_system": "pixels",
                    "artifact": {"sha256": artifact_sha},
                }
            ),
            encoding="utf-8",
        )
        manifest = self.root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "renderer": "matplotlib",
                    "artifact": {"path": str(candidate), "sha256": artifact_sha},
                    "chart_spec": {
                        "path": str(spec),
                        "sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
                    },
                    "layout_metadata": {
                        "path": str(layout),
                        "sha256": hashlib.sha256(layout.read_bytes()).hexdigest(),
                    },
                }
            ),
            encoding="utf-8",
        )
        self.run_cli(
            "iterate",
            "--session",
            "test-session",
            "--output",
            candidate,
            "--bundle-manifest",
            manifest,
        )
        recorded = self.status()["iterations"][-1]
        inspection = self.root / "inspection.json"
        inspection.write_text(
            json.dumps(
                {
                    "artifact": {
                        "path": str(candidate),
                        "sha256": recorded["artifact"]["sha256"],
                    },
                    "layout_metadata": {
                        "path": str(layout),
                        "sha256": hashlib.sha256(layout.read_bytes()).hexdigest(),
                    },
                    "checks_complete": True,
                    "passes_geometry_checks": False,
                    "defects": [
                        {
                            "code": "ANNOTATION_SERIES_COLLISION",
                            "severity": "high",
                            "element_ids": ["event", "series"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.run_cli(
            "inspect", "--session", "test-session", "--report", inspection
        )
        recorded = self.status()["iterations"][-1]
        self.assertTrue(Path(recorded["render_bundle"]["chart_spec"]["path"]).is_file())
        self.assertEqual(
            recorded["inspection"]["defect_codes"],
            ["ANNOTATION_SERIES_COLLISION"],
        )
        request = json.loads(
            self.run_cli("review-request", "--session", "test-session").stdout
        )
        packet = json.loads(Path(request["request"]).read_text(encoding="utf-8"))
        self.assertEqual(
            packet["deterministic_inspection"]["sha256"],
            recorded["inspection"]["sha256"],
        )

    def test_inspection_rejects_layout_metadata_for_another_artifact(self):
        self.start()
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        iteration = self.status()["iterations"][-1]
        layout = self.root / "wrong-layout.json"
        layout.write_text(
            json.dumps({"artifact": {"sha256": "0" * 64}}),
            encoding="utf-8",
        )
        inspection = self.root / "inspection.json"
        inspection.write_text(
            json.dumps(
                {
                    "artifact": iteration["artifact"],
                    "layout_metadata": {
                        "path": str(layout),
                        "sha256": hashlib.sha256(layout.read_bytes()).hexdigest(),
                    },
                    "checks_complete": True,
                    "passes_geometry_checks": True,
                    "defects": [],
                }
            ),
            encoding="utf-8",
        )
        rejected = self.run_cli(
            "inspect",
            "--session",
            "test-session",
            "--report",
            inspection,
            ok=False,
        )
        self.assertIn("does not match the recorded iteration artifact", rejected.stderr)

    def test_send_cannot_override_known_deterministic_defect(self):
        self.start()
        bundle = render_chart(
            str(FIXTURES),
            str(self.root / "coffee-bad"),
            build_function="coffee_bad",
        )
        self.run_cli(
            "iterate",
            "--session",
            "test-session",
            "--output",
            bundle["artifact"]["path"],
            "--bundle-manifest",
            bundle["manifest_path"],
        )
        inspection = inspect_rendered_chart(
            bundle["artifact"]["path"], bundle["layout_metadata_path"]
        )
        self.run_cli(
            "inspect",
            "--session",
            "test-session",
            "--report",
            inspection["inspection_path"],
        )
        rejected = self.review("Send", ok=False)
        self.assertIn("cannot override deterministic inspection defects", rejected.stderr)

    def test_coffee_mcp_repair_crosses_state_machine_pass_line(self):
        self.start()
        reports = []
        for function, verdict, expected_state in (
            ("coffee_bad", "Revise", "revise"),
            ("coffee_fixed", "Send", "user_review"),
        ):
            bundle = render_chart(
                str(FIXTURES),
                str(self.root / function),
                build_function=function,
            )
            self.ensure_revision_contract()
            self.run_cli(
                "iterate",
                "--session",
                "test-session",
                "--output",
                bundle["artifact"]["path"],
                "--bundle-manifest",
                bundle["manifest_path"],
            )
            inspection = inspect_rendered_chart(
                bundle["artifact"]["path"], bundle["layout_metadata_path"]
            )
            reports.append(inspection)
            self.run_cli(
                "inspect",
                "--session",
                "test-session",
                "--report",
                inspection["inspection_path"],
            )
            result = self.review(verdict)
            self.assertEqual(result["state"], expected_state)

        comparison = compare_chart_artifacts(
            reports[0]["inspection_path"], reports[1]["inspection_path"]
        )
        self.assertTrue(comparison["mechanically_improved"])
        self.assertEqual(comparison["blocking_defect_count"], {"before": 4, "after": 0})
        self.assertEqual(
            self.status()["iterations"][-1]["artifact"]["sha256"],
            reports[1]["artifact"]["sha256"],
        )
        automatic = self.status()["iterations"][-1]["inspection"]["comparison"]
        self.assertEqual(automatic["introduced_defect_codes"], [])
        self.assertIn("ANNOTATION_SERIES_COLLISION", automatic["resolved_defect_codes"])

    def test_evaluation_rejects_the_wrong_deterministic_inspection_hash(self):
        self.start()
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        iteration = self.status()["iterations"][-1]
        inspection = self.root / "inspection.json"
        inspection.write_text(
            json.dumps(
                {
                    "artifact": iteration["artifact"],
                    "layout_metadata": None,
                    "checks_complete": False,
                    "passes_geometry_checks": False,
                    "defects": [],
                }
            ),
            encoding="utf-8",
        )
        self.run_cli("inspect", "--session", "test-session", "--report", inspection)
        rejected = self.review(
            "Revise", inspection_sha_override="0" * 64, ok=False
        )
        self.assertIn("deterministic_inspection_sha256", rejected.stderr)

    def test_duplicate_artifact_is_rejected_under_same_context(self):
        self.start()
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        self.review("Revise")
        self.ensure_revision_contract()
        result = self.run_cli(
            "iterate",
            "--session",
            "test-session",
            "--output",
            candidate,
            ok=False,
        )
        self.assertIn("unchanged from iteration 1", result.stderr)
        self.assertEqual(self.status()["state"], "revise")

    def test_iteration_budget_increase_requires_and_consumes_user_grant(self):
        started = self.start("--max-iterations", "1")
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Revise")
        self.assertEqual(result["state"], "stopped")
        self.assertEqual(self.status()["stop"]["kind"], "iteration_budget")
        premature = self.run_cli(
            "resume",
            "--session",
            "test-session",
            "--reason",
            "Invented continuation reason",
            ok=False,
        )
        self.assertIn("user-authorized limit increase", premature.stderr)
        rejected = self.run_cli(
            "limits",
            "--session",
            "test-session",
            "--max-iterations",
            "2",
            ok=False,
        )
        self.assertIn("user authorization grant", rejected.stderr)

        case_path = Path(started["case_dir"]) / "case.json"
        case = json.loads(case_path.read_text(encoding="utf-8"))
        case["limit_authorizations"].append(
            {
                "id": "grant-from-user-turn",
                "case_id": case["case_id"],
                "at": "2026-08-18T10:00:00+00:00",
                "source": "runtime-user-turn",
                "source_turn_id": "test-user-turn",
                "user_message": "Continue for one more iteration",
                "user_message_sha256": hashlib.sha256(
                    b"Continue for one more iteration"
                ).hexdigest(),
                "authorized_stop_at": case["stop"]["at"],
                "approved_limits": {"max_iterations": 2},
                "consumed_at": None,
                "limit_change_number": None,
            }
        )
        case_path.write_text(json.dumps(case), encoding="utf-8")
        changed = self.run_cli(
            "limits",
            "--session",
            "test-session",
            "--max-iterations",
            "2",
            "--authorization",
            "grant-from-user-turn",
        )
        change = json.loads(changed.stdout)["limit_change"]
        self.assertEqual(change["authorization_id"], "grant-from-user-turn")
        audited = self.status()
        self.assertEqual(audited["limit_authorizations"][0]["limit_change_number"], 1)
        self.assertEqual(audited["limit_changes"][0]["increases"], {"max_iterations": 2})
        self.assertEqual(audited["state"], "stopped")
        reused = self.run_cli(
            "limits",
            "--session",
            "test-session",
            "--max-iterations",
            "3",
            "--authorization",
            "grant-from-user-turn",
            ok=False,
        )
        self.assertIn("already been consumed", reused.stderr)
        resumed = self.run_cli(
            "resume",
            "--session",
            "test-session",
            "--reason",
            "User approved another bounded revision",
        )
        self.assertEqual(json.loads(resumed.stdout)["state"], "revise")

    def test_limits_can_be_viewed_or_tightened_without_authorization(self):
        self.start("--max-iterations", "4")
        viewed = json.loads(
            self.run_cli("limits", "--session", "test-session").stdout
        )
        self.assertEqual(viewed["limits"]["max_iterations"], 4)
        tightened = json.loads(
            self.run_cli(
                "limits",
                "--session",
                "test-session",
                "--max-iterations",
                "2",
            ).stdout
        )
        self.assertEqual(tightened["limits"]["max_iterations"], 2)
        self.assertIsNone(tightened["limit_change"]["authorization_id"])

    def test_reworded_equivalent_actions_deduplicate_and_stall(self):
        self.start("--max-iterations", "3", "--max-stalled-evaluations", "1")
        self.iterate(self.write_png("candidate-1.png", b"candidate-1"))
        self.review(
            "Revise",
            action_override=[
                {
                    "target": "Chat delivery width",
                    "from": "The preview is too wide at delivery size",
                    "to": "The chart reads in the compact chat viewport",
                    "why": "Readers should not need to expand the canvas",
                    "codes": ["R3"],
                    "affected_zones": ["plot"],
                }
            ],
        )
        self.iterate(self.write_png("candidate-2.png", b"candidate-2"))
        result = self.review(
            "Revise",
            carry_forward_result="Concern",
            action_override=[
                {
                    "target": "Compact preview size",
                    "from": "The canvas still exceeds the chat width",
                    "to": "Scale it for the delivery viewport",
                    "why": "The chart must work without opening a larger display",
                    "codes": ["R3"],
                    "affected_zones": ["plot"],
                }
            ],
        )
        self.assertEqual(result["state"], "blocked")
        status = self.status()
        self.assertEqual(status["stop"]["kind"], "no_progress")
        self.assertEqual(len(status["evaluations"][-1]["open_required_actions"]), 1)
        self.assertNotIn(
            "equivalent_reports",
            status["evaluations"][0]["open_required_actions"][0],
        )
        self.assertEqual(
            status["evaluations"][-1]["open_required_actions"][0][
                "equivalent_reports"
            ][0]["evaluation"],
            2,
        )
        self.assertEqual(status["stalled_evaluations"], 1)

    def test_distinct_actions_remain_distinct(self):
        self.start("--max-iterations", "3", "--max-stalled-evaluations", "3")
        self.iterate(self.write_png("candidate-1.png", b"candidate-1"))
        self.review(
            "Revise",
            action_override=[
                {
                    "target": "Legend",
                    "from": "The legend is incomplete",
                    "to": "Every series is identified",
                    "why": "Readers must identify each series",
                    "codes": ["R3"],
                    "affected_zones": ["legend"],
                }
            ],
        )
        self.iterate(self.write_png("candidate-2.png", b"candidate-2"))
        self.review(
            "Revise",
            carry_forward_result="Concern",
            action_override=[
                {
                    "target": "Axis ticks",
                    "from": "The axis labels overlap",
                    "to": "Every tick label is legible",
                    "why": "Values must be readable",
                    "codes": ["R3"],
                    "affected_zones": ["axis"],
                }
            ],
        )
        actions = self.status()["evaluations"][-1]["open_required_actions"]
        self.assertEqual(len(actions), 2)
        self.assertEqual({item["action"]["affected_zones"][0] for item in actions}, {"legend", "axis"})

    def test_final_evaluation_and_status_do_not_reopen_budget_stop(self):
        self.start("--max-iterations", "1")
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Revise")
        self.assertEqual(result["state"], "stopped")
        before = self.status()
        after = self.status()
        self.assertEqual(after["state"], "stopped")
        self.assertEqual(after["stop"]["kind"], "iteration_budget")
        self.assertEqual(after["transitions"], before["transitions"])

    def test_repeated_gate_signature_blocks_for_no_progress(self):
        self.start("--max-iterations", "3", "--max-stalled-evaluations", "1")
        self.iterate(self.write_png("candidate-1.png", b"candidate-1"))
        self.review("Revise")
        self.iterate(self.write_png("candidate-2.png", b"candidate-2"))
        result = self.review("Revise")
        self.assertEqual(result["state"], "blocked")
        status = self.status()
        self.assertEqual(status["stop"]["kind"], "no_progress")
        self.assertEqual(status["best_candidate"]["iteration"], 1)

    def test_explicit_stop_and_resume_preserve_case(self):
        started = self.start()
        stopped = self.run_cli(
            "stop",
            "--session",
            "test-session",
            "--kind",
            "user_stop",
            "--reason",
            "User paused the run",
        )
        self.assertEqual(json.loads(stopped.stdout)["state"], "stopped")
        resumed = self.run_cli(
            "resume",
            "--session",
            "test-session",
            "--reason",
            "User returned",
        )
        self.assertEqual(json.loads(resumed.stdout)["state"], "build")
        self.assertEqual(self.status()["case_id"], started["case_id"])

    def test_send_waits_for_user_acceptance(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Send")
        self.assertEqual(result["state"], "user_review")
        accepted = self.run_cli("accept", "--session", "test-session")
        self.assertIn("accepted", json.loads(accepted.stdout))
        self.assertEqual(self.status()["state"], "accepted")

    def test_narrative_partial_normalizes_to_gate_concern(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        self.review("Revise", insight_result="Partial")
        stored = self.status()["evaluations"][0]
        self.assertEqual(stored["gates"]["Insight"], "Concern")

    def test_release_check_requires_named_stress_test(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        rejected = self.review("Revise", omit_release_stress_test=True, ok=False)
        self.assertIn("Visual integrity.stress_test", rejected.stderr)

    def test_review_requires_both_presentation_checks(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        rejected = self.review(
            "Revise", omit_presentation_check="Copy style", ok=False
        )
        self.assertIn("presentation_checks.Copy style", rejected.stderr)

    def test_iteration_recorded_before_presentation_gate_remains_reviewable(self):
        started = self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        case_path = Path(started["case_dir"]) / "case.json"
        case = json.loads(case_path.read_text(encoding="utf-8"))
        case["iterations"][-1].pop("presentation_checks_required")
        case_path.write_text(json.dumps(case), encoding="utf-8")
        result = self.review("Send", omit_presentation_section=True)
        self.assertEqual(result["verdict"], "Send")

    def test_unresolved_evaluator_action_cannot_disappear(self):
        self.start("--max-iterations", "3")
        self.iterate(self.write_png("candidate-1.png", b"candidate-1"))
        self.review("Revise")
        first = self.status()["evaluations"][0]
        self.assertEqual(len(first["open_required_actions"]), 1)

        self.iterate(self.write_png("candidate-2.png", b"candidate-2"))
        rejected = self.review("Send", carry_forward_result="Concern", ok=False)
        self.assertIn("Send requires every required gate", rejected.stderr)
        self.assertEqual(self.status()["state"], "context_reveal")

    def test_token_budget_blocks_the_next_build(self):
        self.start("--max-tokens", "10")
        self.run_cli(
            "usage",
            "--session",
            "test-session",
            "--stage",
            "creator",
            "--input-tokens",
            "11",
        )
        result = self.run_cli(
            "build-check",
            "--session",
            "test-session",
            ok=False,
        )
        self.assertIn("token budget exhausted", result.stderr)
        self.assertEqual(self.status()["stop"]["kind"], "token_budget")

    def test_completed_artifact_is_preserved_when_one_call_crosses_budget(self):
        self.start("--max-tokens", "10")
        self.run_cli("build-check", "--session", "test-session")
        self.run_cli(
            "usage",
            "--session",
            "test-session",
            "--stage",
            "creator",
            "--iteration",
            "1",
            "--input-tokens",
            "11",
        )
        iteration = self.iterate(self.write_png("candidate.png", b"candidate"))
        self.assertEqual(iteration["iteration"], 1)
        self.assertEqual(self.status()["state"], "blind_review")
        self.assertTrue(self.status()["telemetry"]["events"][0]["planned_iteration"])

    def test_cached_input_tokens_are_not_double_counted(self):
        self.start()
        self.run_cli(
            "usage",
            "--session",
            "test-session",
            "--stage",
            "creator",
            "--input-tokens",
            "100",
            "--cached-input-tokens",
            "80",
            "--output-tokens",
            "20",
        )
        telemetry = self.status()["telemetry"]
        self.assertEqual(telemetry["input_tokens"], 100)
        self.assertEqual(telemetry["cached_input_tokens"], 80)
        self.assertEqual(telemetry["total_tokens"], 120)

    def test_cost_budget_blocks_the_next_build(self):
        self.start("--max-cost-usd", "0.10")
        self.run_cli(
            "usage",
            "--session",
            "test-session",
            "--stage",
            "creator",
            "--cost-usd",
            "0.11",
        )
        result = self.run_cli(
            "build-check",
            "--session",
            "test-session",
            ok=False,
        )
        self.assertIn("cost budget exhausted", result.stderr)
        self.assertEqual(self.status()["stop"]["kind"], "cost_budget")

    def test_elapsed_time_budget_blocks_the_next_build(self):
        started = self.start("--max-elapsed-minutes", "1")
        case_path = Path(started["case_dir"]) / "case.json"
        case = json.loads(case_path.read_text(encoding="utf-8"))
        case["created_at"] = "2000-01-01T00:00:00+00:00"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        result = self.run_cli(
            "build-check",
            "--session",
            "test-session",
            ok=False,
        )
        self.assertIn("time budget exhausted", result.stderr)
        self.assertEqual(self.status()["stop"]["kind"], "time_budget")

    def test_context_update_supersedes_verdict_and_allows_same_artifact(self):
        self.start("--max-iterations", "3", "--audience", "General reader")
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        self.review("Revise")
        updated = self.run_cli(
            "context",
            "--session",
            "test-session",
            "--text",
            "This is for an investment committee.",
            "--audience",
            "Investment committee",
            "--purpose",
            "Decide which sectors need discussion",
        )
        payload = json.loads(updated.stdout)
        self.assertEqual(payload["context_version"], 2)
        self.assertEqual(payload["state"], "critique")
        self.record_semantic_preflight()
        second = self.iterate(candidate, "Same artifact under changed context")
        self.assertEqual(second["iteration"], 2)
        status = self.status()
        self.assertEqual(status["iterations"][1]["context_version"], 2)
        self.assertEqual(status["evaluations"][0]["superseded_by_context_version"], 2)

    def test_context_change_cancels_inflight_review_without_deleting_artifact(self):
        self.start("--max-iterations", "3")
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        self.ensure_inspection()
        self.run_cli("review-request", "--session", "test-session")
        updated = self.run_cli(
            "context",
            "--session",
            "test-session",
            "--message",
            "The losses are broader than the gains",
        )
        self.assertEqual(json.loads(updated.stdout)["state"], "critique")
        status = self.status()
        self.assertIn("cancelled_at", status["iterations"][0])
        self.assertTrue(Path(status["iterations"][0]["artifact"]["path"]).exists())
        self.record_semantic_preflight()
        second = self.iterate(candidate, "Reassess under context version 2")
        self.assertEqual(second["iteration"], 2)

    def test_reveal_uses_versioned_context_and_provenance(self):
        self.start(
            "--context-source",
            "user",
            "--audience",
            "General reader",
            "--purpose",
            "Explain the weekly ranking",
            "--hypothesis",
            "Losses are more extreme than gains",
        )
        self.run_cli(
            "feedback",
            "--session",
            "test-session",
            "--text",
            "Keep category labels close to their bars",
            "--target",
            "Category-to-bar relationship",
            "--current",
            "Labels are separated by blank space",
            "--required",
            "Each label is adjacent or visibly connected to its bar",
            "--why",
            "Readers should not trace across competing rows",
        )
        self.iterate(self.write_png("candidate.png", b"candidate"))
        self.ensure_inspection()
        request_output = self.run_cli("review-request", "--session", "test-session")
        request = json.loads(request_output.stdout)
        status = self.status()
        iteration = status["iterations"][-1]
        blind = {
            "reviewer": "reviewer-agent",
            "iteration": iteration["number"],
            "artifact_sha256": iteration["artifact"]["sha256"],
            "expert": "Blind expert read",
            "audience": "Blind audience read",
            "semantics": self.blind_semantics(),
        }
        Path(request["blind_response"]).write_text(json.dumps(blind), encoding="utf-8")
        reveal_output = self.run_cli("blind-submit", "--session", "test-session")
        reveal = json.loads(
            Path(json.loads(reveal_output.stdout)["reveal"]).read_text(encoding="utf-8")
        )
        self.assertEqual(reveal["context_version"], 1)
        self.assertEqual(reveal["context"]["fields"]["purpose"]["value"], "Explain the weekly ranking")
        self.assertEqual(reveal["context"]["fields"]["purpose"]["source"], "user")
        self.assertEqual(reveal["context"]["fields"]["brand"]["source"], "unknown")
        self.assertEqual(
            reveal["active_acceptance_checks"][0]["target"],
            "Category-to-bar relationship",
        )

    def test_preservation_contract_becomes_an_intake_release_check(self):
        self.start("--preserve", "title, source note, and all plotted values")
        self.iterate(self.write_png("candidate.png", b"candidate"))
        self.ensure_inspection()
        request_output = self.run_cli("review-request", "--session", "test-session")
        request = json.loads(request_output.stdout)
        status = self.status()
        iteration = status["iterations"][-1]
        blind = {
            "reviewer": "reviewer-agent",
            "iteration": iteration["number"],
            "artifact_sha256": iteration["artifact"]["sha256"],
            "expert": "Blind expert read",
            "audience": "Blind audience read",
            "semantics": self.blind_semantics(),
        }
        Path(request["blind_response"]).write_text(json.dumps(blind), encoding="utf-8")
        reveal_output = self.run_cli("blind-submit", "--session", "test-session")
        reveal = json.loads(
            Path(json.loads(reveal_output.stdout)["reveal"]).read_text(encoding="utf-8")
        )
        self.assertEqual(reveal["active_acceptance_checks"][0]["id"], "r1")
        self.assertEqual(reveal["active_acceptance_checks"][0]["kind"], "preserve")
        self.assertIn("title, source note", reveal["active_acceptance_checks"][0]["required"])

    def test_intake_change_check_must_precede_first_iteration(self):
        self.start()
        self.run_cli(
            "check",
            "--session",
            "test-session",
            "--kind",
            "change",
            "--text",
            "Remove the legend and label each series at its mark",
            "--target",
            "Series identification",
            "--current",
            "Readers must look up the legend",
            "--required",
            "No legend remains and every series is named at its mark",
        )
        self.iterate(self.write_png("candidate.png", b"candidate"))
        rejected = self.run_cli(
            "check",
            "--session",
            "test-session",
            "--kind",
            "change",
            "--text",
            "Late intake check",
            "--target",
            "Legend",
            "--current",
            "Present",
            "--required",
            "Absent",
            ok=False,
        )
        self.assertIn("case state is 'blind_review'", rejected.stderr)

    def test_iteration_requires_current_semantic_preflight(self):
        self.run_cli(
            "start",
            "--session",
            "test-session",
            "--image",
            self.original,
            "--creator",
            "creator-agent",
        )
        rejected = self.run_cli(
            "iterate",
            "--session",
            "test-session",
            "--output",
            self.write_png("candidate.png", b"candidate"),
            ok=False,
        )
        self.assertIn("case state is 'critique'", rejected.stderr)

    def test_review_request_requires_exact_artifact_inspection(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        rejected = self.run_cli(
            "review-request", "--session", "test-session", ok=False
        )
        self.assertIn("Inspect the exact recorded artifact", rejected.stderr)

    def test_auto_renderer_rejects_unexplained_matplotlib_when_ggplot_is_supported(self):
        self.start()
        report = self.root / "bad-renderer.json"
        report.write_text(
            json.dumps(
                {
                    "requested": "auto",
                    "selected": "matplotlib",
                    "ggplot2_supported": True,
                    "reason": "",
                    "probe": {
                        "renderers": {
                            "ggplot2": {"available": True, "failure_reasons": []},
                            "matplotlib": {"available": True},
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        rejected = self.run_cli(
            "renderer-selection",
            "--session",
            "test-session",
            "--report",
            report,
            ok=False,
        )
        self.assertIn("Auto renderer must select ggplot2", rejected.stderr)

    def test_redesign_cannot_build_until_new_critique_and_design_contract(self):
        self.start("--max-iterations", "3")
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Redesign")
        self.assertEqual(result["state"], "redesign")
        rejected = self.run_cli(
            "iterate",
            "--session",
            "test-session",
            "--output",
            self.write_png("candidate-2.png", b"candidate-2"),
            ok=False,
        )
        self.assertIn("case state is 'redesign'", rejected.stderr)

    def test_structured_intake_context_defaults_to_inferred(self):
        self.start("--audience", "General reader", "--message", "A directional claim")
        context = self.status()["context"]["fields"]
        self.assertEqual(context["audience"]["source"], "inferred")
        self.assertEqual(context["message"]["source"], "inferred")

    def test_send_requires_every_semantic_dimension_to_pass(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Send", semantic_result="Concern", ok=False)
        self.assertIn("Send requires", result.stderr)

    def test_send_requires_colour_and_copy_presentation_checks_to_pass(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Send", presentation_result="Concern", ok=False)
        self.assertIn("Send requires", result.stderr)

    def test_reveal_cannot_rewrite_frozen_blind_semantics(self):
        self.start()
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Revise", tamper_blind_semantics=True, ok=False)
        self.assertIn("blind semantics must match", result.stderr)

    def test_paused_execution_miss_requires_enforcement_and_regression_test(self):
        self.start()
        self.run_cli(
            "stop",
            "--session",
            "test-session",
            "--kind",
            "user_stop",
            "--reason",
            "User rejected the workflow result",
        )
        rejected = self.run_cli(
            "diagnose",
            "--session",
            "test-session",
            "--classification",
            "execution-miss",
            "--owner",
            "dataviz-eval",
            "--lesson",
            "A clear rule was not applied",
            ok=False,
        )
        self.assertIn("another prose rule is not a control", rejected.stderr)
        self.run_cli(
            "diagnose",
            "--session",
            "test-session",
            "--classification",
            "execution-miss",
            "--owner",
            "dataviz-eval",
            "--lesson",
            "A clear rule was not applied",
            "--enforcement",
            "Freeze structured semantics before intent reveal",
            "--regression-test",
            "test_reveal_cannot_rewrite_frozen_blind_semantics",
            "--changed-files",
            "dataviz-fix/scripts/case_manager.py,dataviz-fix/tests/test_case_manager.py",
        )
        status = self.status()
        self.assertEqual(status["state"], "stopped")
        self.assertIsNone(status["acceptance"])
        self.assertEqual(status["diagnoses"][0]["classification"], "execution-miss")
        self.assertIn("Freeze structured", status["diagnoses"][0]["enforcement"])

    def test_send_requires_every_active_user_acceptance_check_to_pass(self):
        self.start()
        self.run_cli(
            "feedback",
            "--session",
            "test-session",
            "--text",
            "Keep labels clear of marks",
            "--target",
            "Label-to-mark separation",
            "--current",
            "A label touches a comparison line",
            "--required",
            "Every label has visible clearance or contrasting in-mark placement",
        )
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Send", acceptance_result="Concern", ok=False)
        self.assertIn("Send requires", result.stderr)

    def test_later_feedback_can_supersede_an_earlier_check(self):
        self.start()
        self.run_cli(
            "feedback",
            "--session",
            "test-session",
            "--text",
            "Put every label outside",
            "--target",
            "Label placement",
            "--current",
            "Some labels are inside marks",
            "--required",
            "All labels sit outside",
        )
        self.run_cli(
            "feedback",
            "--session",
            "test-session",
            "--text",
            "Inside labels are valid with contrast and padding",
            "--target",
            "Label legibility",
            "--current",
            "Placement was judged categorically",
            "--required",
            "Each label is legible and clearly bound to its mark",
            "--supersedes",
            "1",
        )
        self.iterate(self.write_png("candidate.png", b"candidate"))
        self.review("Send")
        status = self.status()
        self.assertEqual(status["feedback"][0]["superseded_by_feedback"], 2)
        self.assertEqual(
            [item["id"] for item in status["evaluations"][0]["acceptance_checks"]],
            ["f2"],
        )

    def test_user_feedback_can_supersede_a_conflicting_evaluator_action(self):
        self.start("--max-iterations", "3")
        self.iterate(self.write_png("candidate-1.png", b"candidate-1"))
        self.review("Revise")
        self.run_cli(
            "feedback",
            "--session",
            "test-session",
            "--text",
            "Remove the legend; do not restore it as a fallback",
            "--target",
            "Legend",
            "--current",
            "The evaluator allowed a restored legend",
            "--required",
            "The legend is absent and direct labels carry every identity",
            "--supersedes-actions",
            "e1-a1",
        )
        self.iterate(self.write_png("candidate-2.png", b"candidate-2"))
        self.review("Send")
        second = self.status()["evaluations"][1]
        self.assertEqual(second["carry_forward_checks"], [])
        self.assertEqual([item["id"] for item in second["acceptance_checks"]], ["f1"])

    def test_noop_context_update_does_not_create_a_new_version(self):
        self.start("--context-source", "user", "--audience", "General reader")
        result = self.run_cli(
            "context",
            "--session",
            "test-session",
            "--audience",
            "General reader",
            ok=False,
        )
        self.assertIn("no material change", result.stderr)
        self.assertEqual(self.status()["context_version"], 1)

    def test_legacy_active_case_is_upgraded_in_memory(self):
        started = self.start()
        case_path = Path(started["case_dir"]) / "case.json"
        case = json.loads(case_path.read_text(encoding="utf-8"))
        for name in (
            "context",
            "context_history",
            "limits",
            "telemetry",
            "transitions",
            "best_candidate",
            "stop",
            "stalled_evaluations",
            "stall_keys",
            "limit_authorizations",
            "limit_changes",
        ):
            case.pop(name, None)
        case["schema_version"] = 4
        case["state"] = "active"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        status = self.status()
        self.assertEqual(status["schema_version"], 16)
        self.assertEqual(status["state"], "build")
        self.assertEqual(status["context_version"], 1)
        self.assertIsNone(status["limits"]["max_iterations"])
        self.assertEqual(status["limit_authorizations"], [])
        self.assertEqual(status["limit_changes"], [])


if __name__ == "__main__":
    unittest.main()
