import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "codex" / "scripts" / "case_manager.py"
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
        return json.loads(output.stdout)

    def status(self):
        output = self.run_cli("status", "--session", "test-session")
        return json.loads(output.stdout)

    def iterate(self, path, summary="candidate"):
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

    def review(
        self,
        verdict="Revise",
        carry_forward_result="Pass",
        acceptance_result="Pass",
        insight_result=None,
        omit_release_stress_test=False,
        ok=True,
    ):
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
        if omit_release_stress_test:
            release_checks["Visual integrity"].pop("stress_test")
        codes = []
        actions = []
        if verdict in ("Revise", "Redesign"):
            gates["Visual reasoning"]["result"] = "Concern"
            release_checks["Spatial economy"]["result"] = "Concern"
            codes = ["R3"]
            actions = ["Improve the chart geometry"]
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
            "context_version": iteration.get("context_version", 1),
            "scope": "Source fidelity at screen size",
            "tested_size": "1200 px wide",
            "blind_reads": {"expert": blind["expert"], "audience": blind["audience"]},
            "gates": gates,
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
            "verdict": verdict,
            "codes": codes,
            "required_actions": actions,
        }
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

    def test_duplicate_artifact_is_rejected_under_same_context(self):
        self.start()
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        self.review("Revise")
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

    def test_iteration_budget_stops_and_can_be_extended(self):
        self.start("--max-iterations", "1")
        self.iterate(self.write_png("candidate.png", b"candidate"))
        result = self.review("Revise")
        self.assertEqual(result["state"], "stopped")
        self.assertEqual(self.status()["stop"]["kind"], "iteration_budget")
        self.run_cli(
            "limits",
            "--session",
            "test-session",
            "--max-iterations",
            "2",
        )
        resumed = self.run_cli(
            "resume",
            "--session",
            "test-session",
            "--reason",
            "User approved another bounded revision",
        )
        self.assertEqual(json.loads(resumed.stdout)["state"], "revise")

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
        self.assertEqual(payload["state"], "revise")
        second = self.iterate(candidate, "Same artifact under changed context")
        self.assertEqual(second["iteration"], 2)
        status = self.status()
        self.assertEqual(status["iterations"][1]["context_version"], 2)
        self.assertEqual(status["evaluations"][0]["superseded_by_context_version"], 2)

    def test_context_change_cancels_inflight_review_without_deleting_artifact(self):
        self.start("--max-iterations", "3")
        candidate = self.write_png("candidate.png", b"candidate")
        self.iterate(candidate)
        self.run_cli("review-request", "--session", "test-session")
        updated = self.run_cli(
            "context",
            "--session",
            "test-session",
            "--message",
            "The losses are broader than the gains",
        )
        self.assertEqual(json.loads(updated.stdout)["state"], "revise")
        status = self.status()
        self.assertIn("cancelled_at", status["iterations"][0])
        self.assertTrue(Path(status["iterations"][0]["artifact"]["path"]).exists())
        second = self.iterate(candidate, "Reassess under context version 2")
        self.assertEqual(second["iteration"], 2)

    def test_reveal_uses_versioned_context_and_provenance(self):
        self.start(
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
        self.start("--audience", "General reader")
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
        ):
            case.pop(name, None)
        case["schema_version"] = 4
        case["state"] = "active"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        status = self.status()
        self.assertEqual(status["schema_version"], 9)
        self.assertEqual(status["state"], "build")
        self.assertEqual(status["context_version"], 1)
        self.assertEqual(status["limits"]["max_iterations"], 3)


if __name__ == "__main__":
    unittest.main()
