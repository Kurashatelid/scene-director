"""Contract outcomes on small scenes; run: python3 -m unittest discover -s tests."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1] / "scene-director"
SCRIPT = PACKAGE / "scripts" / "validate_scene.py"
SPEC = importlib.util.spec_from_file_location("validate_scene", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SceneContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        (self.project / "street.html").write_text("<canvas></canvas>")
        (self.project / "identity.png").write_bytes(b"fixture: presence only, not decoded media")
        self.template = json.loads((PACKAGE / "references" / "scene-template.json").read_text())
        self.scene = copy.deepcopy(self.template)
        c = self.scene["active_contract"]
        c.update(id="example-v001", status="ready", duration_sec=15, aspect_ratio="21:9", next_action="render_previz")
        c["scope"].update(allowed_actions=["render_previz"], stop_after="show_full_rough_pass")
        c["previz"].update(engine="Three.js", engine_version="installed", check_questions=["Does the passenger remain seated as the taxi leaves?"], stop_criteria=["Full rough pass covers boarding and departure."])
        c["selected_artifacts"] = [dict(id="street", kind="scene", role="previz_project", path="street.html", essential=True, selection_status="working_selected", user_accepted=False)]
        c["role_coverage"] = [dict(name="@Street", coverage="existing", artifact_ids=["street"])]

    def report(self):
        return MODULE.validate_scene(self.scene, self.project)

    def codes(self, report):
        return {f["code"] for f in report["findings"]}

    def image_route(self):
        c = self.scene["active_contract"]
        c["selected_artifacts"].append(dict(id="identity", kind="image", role="identity", path="identity.png", essential=True, selection_status="working_selected", user_accepted=False))
        c["route"].update(service="Usuals Studio", model="bytedance/seedance-2.5", input_strategy="image_only", video_required=False, settings={"quality": "480p", "audio": True}, inputs=[dict(artifact_id="identity", kind="image", role="identity", provider_asset_id="studio-image-1", input_token="@img1")])
        return c

    def temporal_scene(self):
        c = self.scene["active_contract"]
        c["temporal_constraints"] = [dict(id="boarding", before=["taxi_stopped", "door_opened"], event="passenger_seated", after=["door_closed", "taxi_departed"])]
        c["observations"]["events"] = [dict(id=k, time_sec=t) for k, t in [("taxi_stopped", 2.75), ("door_opened", 3.1), ("passenger_seated", 4.15), ("door_closed", 4.55), ("taxi_departed", 4.65)]]
        return c

    def wet_scene(self):
        c = self.scene["active_contract"]
        c["temporal_constraints"] = [dict(id="wet_coat", before=[], event="splash", after=["handoff"], state=dict(name="coat_wet", before=False, after=True), persistence=dict(until_event="handoff", value=True))]
        c["observations"]["events"] = [dict(id="splash", time_sec=2.5), dict(id="handoff", time_sec=8.8)]
        c["observations"]["states"] = [dict(name="coat_wet", time_sec=t, value=value) for t, value in [(1.75, False), (2.75, True), (8.8, True)]]
        return c

    def test_blank_template_is_incomplete_not_failure_or_success(self):
        report = MODULE.validate_scene(self.template, self.project)
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertEqual(report["counts"]["fail"], 0)
        self.assertFalse(report["visual_or_audio_quality_inferred"])

    def test_ready_local_contract_can_be_consistent_without_claiming_visual_quality(self):
        self.assertEqual(self.report()["status"], "PASS")
        self.assertFalse(self.report()["visual_or_audio_quality_inferred"])
        self.assertFalse(self.scene["active_contract"]["user_selection"]["accepted"])

    def test_current_animatic_requires_engine_questions_and_stop_criteria(self):
        c = self.scene["active_contract"]
        c["previz"].update(engine=None, check_questions=[], stop_criteria=[])
        report = self.report()
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertIn("PREVIZ_ENGINE_NOT_SELECTED", self.codes(report))
        self.assertIn("PREVIZ_CRITERIA_NOT_SELECTED", self.codes(report))

    def test_description_only_needs_no_previz_or_quote_and_cannot_generate(self):
        c = self.scene["active_contract"]
        c["scope"]["allowed_actions"] = ["description_only"]
        c.update(next_action="description_only", previz={})
        self.assertEqual(self.report()["status"], "PASS")
        c["next_action"] = "paid_generation"
        self.assertIn("NEXT_ACTION_OUTSIDE_SCOPE", self.codes(self.report()))
        for action in ("wait_for_user", "complete"):
            c["next_action"] = action
            self.assertEqual(self.report()["status"], "PASS")

    def test_observed_image_only_route_cannot_still_require_video(self):
        c = self.image_route()
        c["route"]["video_required"] = True
        report = self.report()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("VIDEO_REQUIRED_WITHOUT_VIDEO", self.codes(report))

    def test_local_check_cannot_be_attached_as_motion_input(self):
        c = self.image_route()
        (self.project / "motion.mp4").write_bytes(b"presence fixture")
        c["selected_artifacts"].append(dict(id="motion", kind="video", path="motion.mp4", essential=True))
        c["route"].update(input_strategy="video_guided", video_required=True)
        c["route"]["inputs"].append(dict(artifact_id="motion", kind="video", role="motion"))
        self.assertIn("PREVIZ_PURPOSE_CONTRADICTION", self.codes(self.report()))
        c["previz"]["role"] = "generator_motion_input"
        self.assertEqual(self.report()["status"], "PASS")

    def test_selected_engine_and_settings_cannot_conflict(self):
        self.scene["active_contract"]["previz"]["settings"]["engine"] = "Blender"
        self.assertIn("PREVIZ_ENGINE_MISMATCH", self.codes(self.report()))

    def test_missing_essential_selected_file_is_failure(self):
        (self.project / "street.html").unlink()
        report = self.report()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("MISSING_ARTIFACT", self.codes(report))

    def test_text_only_and_intentionally_skipped_references_are_valid(self):
        c = self.scene["active_contract"]
        c["role_coverage"] += [dict(name="@Taxi", coverage="text_only", description="Yellow NYC taxi with plain TAXI roof sign."), dict(name="@Cafe", coverage="intentionally_skipped", reason="User chose to reuse the selected street artwork.")]
        self.assertEqual(self.report()["status"], "PASS")

    def test_old_history_and_unidentified_legacy_mirrors_do_not_block(self):
        self.scene["contract_history"] = [{"id": "old", "route": {"video_required": True, "input_strategy": "image_only", "inputs": []}}]
        self.scene["provider_comparison"] = {"video_mandatory": True, "selected_route": "old image-only route"}
        self.scene["review"] = {"video_viewed": False, "issues": ["Sound not created"]}
        self.scene["previz"] = {"engine": "Blender", "role": "generator_motion_input", "contract_id": "old"}
        self.assertEqual(self.report()["status"], "PASS")

    def test_explicit_same_contract_mirror_must_agree(self):
        self.scene["previz"] = {"contract_id": "example-v001", "engine": "Blender"}
        self.assertIn("CURRENT_MIRROR_MISMATCH", self.codes(self.report()))

    def test_quote_and_bindings_are_for_exact_current_request(self):
        c = self.image_route()
        c["scope"]["allowed_actions"] = ["generate_video"]
        c["next_action"] = "generate_video"
        route = c["route"]
        quote = dict(contract_id=c["id"], service=route["service"], model=route["model"], duration_sec=15, aspect_ratio="7:3", input_strategy="image_only", settings=copy.deepcopy(route["settings"]), input_artifact_ids=["identity"], amount=1.55, currency="USD")
        c["preflight"].update(contract_id=c["id"], input_bindings_verified=True, bindings=copy.deepcopy(route["inputs"]), quote=quote)
        self.assertEqual(self.report()["status"], "PASS")
        quote["duration_sec"] = 10
        c["preflight"]["bindings"][0]["input_token"] = "@img2"
        report = self.report()
        self.assertIn("QUOTE_CONTRACT_MISMATCH", self.codes(report))
        self.assertIn("PREFLIGHT_BINDINGS_MISMATCH", self.codes(report))

    def test_supplied_quote_with_unknown_price_is_unknown_but_zero_is_valid(self):
        c = self.image_route()
        c["preflight"]["quote"] = dict(contract_id=c["id"], service=c["route"]["service"])
        report = self.report()
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertIn("QUOTE_PRICE_UNKNOWN", self.codes(report))
        self.assertIn("QUOTE_CURRENCY_UNKNOWN", self.codes(report))
        c["preflight"]["quote"].update(amount=0, currency="credits")
        self.assertEqual(self.report()["status"], "PASS")

    def test_submit_requires_remaining_capacity_but_prepare_and_completed_do_not(self):
        c = self.scene["active_contract"]
        c["preflight"]["intent"] = "submit"
        report = self.report()
        self.assertEqual(report["execution_capacity"]["remaining_paid_runs"], 0)
        self.assertIn("SUBMISSION_RUN_CAPACITY_EXHAUSTED", self.codes(report))
        c["preflight"]["intent"] = "prepare"
        self.assertEqual(self.report()["status"], "PASS")
        c["execution_limits"].update(max_runs=2, runs_started=1)
        c["preflight"]["intent"] = "submit"
        report = self.report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["execution_capacity"]["remaining_paid_runs"], 1)
        c["execution_limits"].update(max_runs=1, runs_started=1)
        c["preflight"]["intent"] = "completed"
        c["scope"]["allowed_actions"] = ["generate_video"]
        c["next_action"] = "complete"
        report = self.report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["execution_capacity"]["remaining_paid_runs"], 0)
        self.assertNotIn("QUOTE_ABSENT", self.codes(report))

    def test_quote_cannot_exceed_budget_or_invent_credit_conversion(self):
        c = self.image_route()
        c["execution_limits"]["paid_budget"] = dict(amount=2, currency="USD")
        c["preflight"]["quote"] = dict(amount=3.47, currency="USD")
        self.assertIn("PAID_BUDGET_EXCEEDED", self.codes(self.report()))
        c["preflight"]["quote"]["currency"] = "credits"
        report = self.report()
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertIn("BUDGET_UNITS_NOT_COMPARABLE", self.codes(report))

    def test_boarding_order_uses_observed_timestamps(self):
        c = self.temporal_scene()
        self.assertEqual(self.report()["status"], "PASS")
        c["observations"]["events"][-1]["time_sec"] = 4.2
        report = self.report()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("TEMPORAL_ORDER", self.codes(report))

    def test_early_wet_state_before_splash_is_detected(self):
        c = self.wet_scene()
        self.assertEqual(self.report()["status"], "PASS")
        c["observations"]["states"][0]["value"] = True
        report = self.report()
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("TEMPORAL_STATE", self.codes(report))

    def test_wet_state_cannot_disappear_before_handoff(self):
        c = self.wet_scene()
        c["observations"]["states"].insert(2, dict(name="coat_wet", time_sec=5, value=False))
        self.assertIn("STATE_PERSISTENCE", self.codes(self.report()))

    def test_explicit_persistence_end_allows_a_later_state_change(self):
        c = self.wet_scene()
        c["observations"]["states"].append(dict(name="coat_wet", time_sec=14, value=False))
        self.assertEqual(self.report()["status"], "PASS")

    def test_unevidenced_temporal_rule_remains_unknown(self):
        c = self.temporal_scene()
        c["observations"]["events"] = []
        self.assertEqual(self.report()["status"], "UNKNOWN")

    def test_metadata_does_not_establish_claimed_qa(self):
        c = self.scene["active_contract"]
        c["evidence_findings"] = [dict(id="whole_head", status="pass", evidence_refs=[])]
        self.assertEqual(self.report()["status"], "UNKNOWN")

    def test_user_acceptance_of_known_defect_does_not_rewrite_qa(self):
        c = self.scene["active_contract"]
        c["evidence_findings"] = [dict(id="whole_head", status="fail", evidence_refs=["review-frame-1.75s"])]
        c["user_selection"] = dict(artifact_id="street", accepted=True, accepted_known_limits=["whole_head"], evidence_ref="user-message-42")
        self.assertEqual(self.report()["status"], "FAIL")
        self.assertTrue(c["user_selection"]["accepted"])

    def test_qa_summary_compares_only_same_report_and_artifact_ids(self):
        c = self.scene["active_contract"]
        c["reports"] = [dict(id="review-4", artifact_id="street", status="fail")]
        c["qa_summary"] = dict(report_id="review-3", artifact_id="street", status="pass")
        self.assertNotIn("QA_SUMMARY_STALE", self.codes(self.report()))
        c["qa_summary"]["report_id"] = "review-4"
        self.assertIn("QA_SUMMARY_STALE", self.codes(self.report()))

    def test_run_cap_is_enforced(self):
        self.scene["active_contract"]["execution_limits"].update(max_runs=1, runs_started=2)
        self.assertIn("RUN_LIMIT_EXCEEDED", self.codes(self.report()))

    def test_validation_does_not_mutate_input_or_artifact(self):
        before = copy.deepcopy(self.scene)
        file = self.project / "street.html"
        stamp = file.stat().st_mtime_ns
        self.report()
        self.assertEqual(before, self.scene)
        self.assertEqual(stamp, file.stat().st_mtime_ns)
        self.assertEqual(file.read_text(), "<canvas></canvas>")

    def test_cli_returns_json_and_documented_exit_codes(self):
        path = self.project / "scene.json"
        for data, expected_code, expected_status in [(self.template, 3, "UNKNOWN"), (self.scene, 0, "PASS")]:
            path.write_text(json.dumps(data))
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--project-root", str(self.project)], capture_output=True, text=True)
            self.assertEqual(result.returncode, expected_code, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], expected_status)
        path.write_text("{invalid json")
        result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
