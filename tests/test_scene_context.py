import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scene-director/scripts/scene_context.py"
spec = importlib.util.spec_from_file_location("scene_context", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CurrentContextTests(unittest.TestCase):
    def test_current_words_limits_and_unknown_fields_survive_without_history(self):
        contract = {
            "id": "current",
            "utterances": [{"text": "Слова без изменений"}],
            "workflow": {"review_mode": "before_paid", "author_review_status": "awaiting_author"},
            "execution_limits": {"max_runs": 0},
            "future_extension": {"required": True},
        }
        scene = {"schema_version": 3, "active_contract": contract,
                 "contract_history": [{"id": "old", "execution_limits": {"max_runs": 50}}],
                 "jobs": [{"private_payload": "old response"}]}
        result, code = module.current_context(scene, "source.json")
        self.assertEqual(code, 0)
        self.assertEqual(result["active_contract"], contract)
        self.assertNotIn("contract_history", result)
        self.assertNotIn("jobs", result)
        self.assertIn("jobs", result["supplemental_fields"])
        self.assertFalse(result["is_authorization"])

    def test_legacy_and_empty_contracts_require_migration(self):
        for scene in ({"schema_version": 2, "active_contract": {"id": "legacy"}},
                      {"schema_version": 3, "contract_history": [{"id": "old"}]},
                      {"schema_version": 3, "active_contract": {}}):
            result, code = module.current_context(scene, "source.json")
            self.assertEqual(code, 3)
            self.assertIsNone(result["active_contract"])

    def test_closed_scene_marker_is_not_hidden_by_older_ready_contract(self):
        result, code = module.current_context(
            {"schema_version": 3, "status": "abandoned", "stage": "closed_by_user",
             "active_contract": {"id": "old-ready", "status": "ready"}}, "scene.json")
        self.assertEqual(code, 0)
        self.assertEqual(result["scene_status"], "abandoned")
        self.assertEqual(result["stage"], "closed_by_user")
        self.assertFalse(result["is_authorization"])

    def test_cli_does_not_write_source_or_load_historical_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scene.json"
            scene = {"schema_version": 3, "active_contract": {"id": "current", "max_runs": 0},
                     "contract_history": [{"payload": "history " * 10000}]}
            path.write_text(json.dumps(scene))
            before = path.read_bytes()
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(json.loads(run.stdout)["active_contract"], scene["active_contract"])
            self.assertLess(len(run.stdout), len(before) / 10)

    def test_invalid_input_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("[]")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["status"], "INPUT_ERROR")


if __name__ == "__main__":
    unittest.main()
