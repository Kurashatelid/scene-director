#!/usr/bin/env python3
"""Read-only scene contract and explicit-evidence consistency checks (stdlib only).

Usage: python3 scripts/validate_scene.py SCENE_JSON [--project-root PROJECT_DIR]
Relative artifact paths resolve against PROJECT_DIR (default: working directory).
JSON stdout: status PASS / FAIL / UNKNOWN, counts, stable finding codes, and
execution_capacity.remaining_paid_runs (null when limits are unknown).
Exit codes: 0 consistent supplied checks; 1 contradiction; 2 input/JSON/usage error;
3 incomplete/unverified. PASS is neither visual QA nor permission for a paid run.

Only active_contract is current truth. Legacy root fields and contract_history
are retained for compatibility but cannot override it. A root mirror carrying
the SAME contract_id is checked where supported; differently identified history
is ignored. No media decoding, network, generation, repairs, or writes occur.

Temporal constraints use before:[event IDs], event:ID, after:[event IDs]; an
optional state:{name,before,after} and persistence:{until_event,value}. They are
checked against observations.events[{id,time_sec,evidence_ref}] and
observations.states[{name,time_sec,value,evidence_ref}]. Supplied timestamps and
annotated states are evidence inputs, not inferred visual facts. Explicit
evidence_findings use status pass|fail|unknown and evidence_refs:[...].

Previz scope actions: build_previz, render_previz, review_previz, export_previz,
repair_previz. They require a selected previz engine, check_questions and
stop_criteria. next_action must be an allowed action, wait_for_user, or complete.
preflight.intent is prepare (default), submit, or completed. Only submit requires
remaining run capacity; completed does not require a new quote. Every supplied
quote needs an amount and currency (0 is valid; unknown prices stay UNKNOWN).
These checks never infer expense authorization or replace tool confirmation.
"""

import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

PREVIZ_ACTIONS = {"build_previz", "render_previz", "review_previz", "export_previz", "repair_previz"}
GENERATION_ACTIONS = {"generate_video", "generate_image", "paid_generation"}
SENTINEL_ACTIONS = {"wait_for_user", "complete"}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def aspect(value):
    try:
        return Fraction(str(value).replace(":", "/"))
    except (ValueError, ZeroDivisionError):
        return None


class Validator:
    def __init__(self, scene, project_root):
        self.scene = scene
        self.root = Path(project_root)
        self.findings = []
        self.execution_capacity = {"max_runs": None, "runs_started": None, "remaining_paid_runs": None}

    def add(self, status, code, path, message):
        self.findings.append(dict(status=status, code=code, path=path, message=message))

    def obj(self, value, path):
        if not isinstance(value, dict):
            self.add("FAIL", "INVALID_FIELD_TYPE", path, "Expected an object.")
            return {}
        return value

    def rows(self, value, path):
        if not isinstance(value, list):
            self.add("FAIL", "INVALID_FIELD_TYPE", path, "Expected an array.")
            return []
        result = []
        for i, row in enumerate(value):
            if not isinstance(row, dict):
                self.add("FAIL", "INVALID_FIELD_TYPE", f"{path}[{i}]", "Expected an object.")
            else:
                result.append(row)
        return result

    def same(self, observed, expected, path, code):
        for key, value in observed.items():
            if key not in expected:
                continue
            actual = expected[key]
            equal = aspect(value) == aspect(actual) if key == "aspect_ratio" else value == actual
            if not equal:
                self.add("FAIL", code, f"{path}.{key}", f"Does not match the current contract ({key}).")

    def run(self):
        if self.scene.get("schema_version") != 3:
            self.add("UNKNOWN", "SCHEMA_NOT_CURRENT", "schema_version", "Migrate explicitly to schema 3; legacy state is not current truth.")
        if "active_contract" not in self.scene:
            self.add("UNKNOWN", "NO_ACTIVE_CONTRACT", "active_contract", "Current contract is absent; history is not used as a substitute.")
            return self.result(None)
        c = self.obj(self.scene["active_contract"], "active_contract")
        cid = c.get("id")
        for key in ("id", "status", "duration_sec", "aspect_ratio"):
            if c.get(key) in (None, "", []):
                self.add("UNKNOWN", "INCOMPLETE_CONTRACT", f"active_contract.{key}", "Current value has not been selected.")
        if c.get("status") == "draft":
            self.add("UNKNOWN", "DRAFT_CONTRACT", "active_contract.status", "Draft is not a ready or completed contract.")
        duration = c.get("duration_sec")
        if duration is not None and (not number(duration) or duration <= 0):
            self.add("FAIL", "INVALID_DURATION", "active_contract.duration_sec", "Duration must be a positive finite number.")
        if c.get("aspect_ratio") is not None and (aspect(c["aspect_ratio"]) is None or aspect(c["aspect_ratio"]) <= 0):
            self.add("FAIL", "INVALID_ASPECT", "active_contract.aspect_ratio", "Aspect ratio must be positive, for example 21:9.")
        scope = self.obj(c.get("scope", {}), "active_contract.scope")
        actions = scope.get("allowed_actions", [])
        if not isinstance(actions, list) or any(not isinstance(a, str) for a in actions):
            self.add("FAIL", "INVALID_FIELD_TYPE", "active_contract.scope.allowed_actions", "Expected action names in an array.")
            actions = []
        if not actions:
            self.add("UNKNOWN", "SCOPE_NOT_SELECTED", "active_contract.scope.allowed_actions", "No current actions are selected.")
        if not scope.get("stop_after"):
            self.add("UNKNOWN", "STOP_NOT_SELECTED", "active_contract.scope.stop_after", "Current stopping point is not selected.")
        next_action = c.get("next_action")
        if next_action is None or next_action == "":
            self.add("UNKNOWN", "NEXT_ACTION_NOT_SELECTED", "active_contract.next_action", "Select an allowed action or wait_for_user/complete.")
        elif not isinstance(next_action, str) or (next_action not in actions and next_action not in SENTINEL_ACTIONS):
            self.add("FAIL", "NEXT_ACTION_OUTSIDE_SCOPE", "active_contract.next_action", "Current next action is outside the exact allowed actions and wait/complete sentinels.")
        languages = self.obj(c.get("languages", {}), "active_contract.languages")
        for row in self.rows(c.get("utterances", []), "active_contract.utterances"):
            if not row.get("text") or not row.get("speaker"):
                self.add("UNKNOWN", "UTTERANCE_INCOMPLETE", "active_contract.utterances", "An utterance lacks exact text or its speaker.")
            if not row.get("language") and not languages.get("spoken"):
                self.add("UNKNOWN", "LANGUAGE_NOT_SELECTED", "active_contract.languages.spoken", "Spoken language is not selected.")
        artifacts = self.artifacts(c)
        self.route(c, artifacts, actions)
        self.temporal(c, duration)
        self.evidence(c, artifacts)
        self.limits(c)
        # Compare only explicit same-ID current mirrors, never anonymous legacy data.
        mirror = self.scene.get("previz", {})
        if cid and isinstance(mirror, dict) and mirror.get("contract_id") == cid:
            self.same(mirror, c.get("previz", {}), "previz", "CURRENT_MIRROR_MISMATCH")
        return self.result(cid)

    def artifacts(self, c):
        artifacts = {}
        for row in self.rows(c.get("selected_artifacts", []), "active_contract.selected_artifacts"):
            aid = row.get("id")
            if not isinstance(aid, str) or not aid:
                self.add("FAIL", "ARTIFACT_ID_MISSING", "active_contract.selected_artifacts", "Selected artifact needs a unique ID.")
                continue
            if aid in artifacts:
                self.add("FAIL", "DUPLICATE_ARTIFACT_ID", "active_contract.selected_artifacts", f"Duplicate artifact ID: {aid}.")
            artifacts[aid] = row
            path = row.get("path")
            if path and isinstance(path, str):
                file = Path(path).expanduser()
                if not file.is_absolute():
                    file = self.root / file
                if not file.is_file():
                    self.add("FAIL" if row.get("essential") else "UNKNOWN", "MISSING_ARTIFACT", f"active_contract.selected_artifacts.{aid}", "Selected local artifact file does not exist.")
            elif row.get("essential"):
                self.add("UNKNOWN" if row.get("url") or row.get("provider_asset_id") else "FAIL", "ARTIFACT_NOT_LOCAL", f"active_contract.selected_artifacts.{aid}", "Essential artifact has no verified local file.")
            if row.get("selection_status") == "user_accepted" and row.get("user_accepted") is not True:
                self.add("FAIL", "ACCEPTANCE_CONTRADICTION", f"active_contract.selected_artifacts.{aid}", "Working selection is distinct from user acceptance.")
        for row in self.rows(c.get("role_coverage", []), "active_contract.role_coverage"):
            coverage = row.get("coverage")
            if coverage not in {"existing", "selected", "text_only", "intentionally_skipped"}:
                self.add("UNKNOWN", "ROLE_COVERAGE_UNKNOWN", "active_contract.role_coverage", "Role has no explicit coverage decision.")
            elif coverage in {"text_only", "intentionally_skipped"}:
                if not row.get("description") and not row.get("reason"):
                    self.add("UNKNOWN", "ROLE_DECISION_UNEXPLAINED", "active_contract.role_coverage", "Text-only or skipped coverage needs its description or reason.")
            else:
                ids = row.get("artifact_ids", [])
                if not isinstance(ids, list) or not ids:
                    self.add("UNKNOWN", "ROLE_ARTIFACT_UNKNOWN", "active_contract.role_coverage", "Covered role has no selected artifact IDs.")
                else:
                    for aid in ids:
                        if not isinstance(aid, str) or aid not in artifacts:
                            self.add("FAIL", "ROLE_ARTIFACT_MISSING", "active_contract.role_coverage", "Covered role references an absent selected artifact.")
        return artifacts

    def route(self, c, artifacts, actions):
        route = self.obj(c.get("route", {}), "active_contract.route")
        previz = self.obj(c.get("previz", {}), "active_contract.previz")
        if any(action in PREVIZ_ACTIONS for action in actions):
            if not isinstance(previz.get("engine"), str) or not previz["engine"].strip():
                self.add("UNKNOWN", "PREVIZ_ENGINE_NOT_SELECTED", "active_contract.previz.engine", "Current previz work needs a selected engine.")
            for key in ("check_questions", "stop_criteria"):
                values = previz.get(key)
                if not isinstance(values, list) or not values or not all(isinstance(value, str) and value.strip() for value in values):
                    self.add("UNKNOWN", "PREVIZ_CRITERIA_NOT_SELECTED", "active_contract.previz." + key, "Current previz work needs explicit questions and a stopping criterion.")
        inputs = self.rows(route.get("inputs", []), "active_contract.route.inputs")
        videos = []
        for row in inputs:
            aid = row.get("artifact_id")
            artifact = artifacts.get(aid, {}) if isinstance(aid, str) else {}
            if not artifact:
                self.add("FAIL", "INPUT_ARTIFACT_MISSING", "active_contract.route.inputs", "Generator input does not resolve to a selected artifact.")
            kind = row.get("kind", artifact.get("kind"))
            if row.get("kind") and artifact.get("kind") and row["kind"] != artifact["kind"]:
                self.add("FAIL", "INPUT_KIND_MISMATCH", "active_contract.route.inputs", "Input kind differs from selected artifact kind.")
            if kind == "video":
                videos.append(row)
            if row.get("role", artifact.get("role")) in {"motion", "camera_video", "motion_video", "mandatory_motion_video", "previz"}:
                if previz.get("role") == "local_check":
                    self.add("FAIL", "PREVIZ_PURPOSE_CONTRADICTION", "active_contract.previz.role", "Local-check previz is attached as a generator motion input.")
                if row.get("engine") and previz.get("engine") and row["engine"] != previz["engine"]:
                    self.add("FAIL", "PREVIZ_ENGINE_MISMATCH", "active_contract.route.inputs", "Motion input engine differs from the selected previz engine.")
        if route.get("input_strategy") in {"image_only", "single_image", "multi_reference"} and videos:
            self.add("FAIL", "IMAGE_ONLY_WITH_VIDEO", "active_contract.route", "Image-only strategy contains video inputs.")
        if route.get("video_required") is True and not videos:
            self.add("FAIL", "VIDEO_REQUIRED_WITHOUT_VIDEO", "active_contract.route", "Current contract requires video, but its inputs contain none.")
        if previz.get("role") not in (None, "local_check", "generator_motion_input"):
            self.add("FAIL", "INVALID_PREVIZ_ROLE", "active_contract.previz.role", "Use local_check or generator_motion_input.")
        if previz.get("role") == "generator_motion_input" and not videos:
            self.add("FAIL", "MOTION_INPUT_ABSENT", "active_contract.previz.role", "Generator motion input was selected but no video is attached.")
        settings = self.obj(previz.get("settings", {}), "active_contract.previz.settings")
        if settings.get("engine") and previz.get("engine") and settings["engine"] != previz["engine"]:
            self.add("FAIL", "PREVIZ_ENGINE_MISMATCH", "active_contract.previz.settings.engine", "Settings identify a different previz engine.")
        preflight = self.obj(c.get("preflight", {}), "active_contract.preflight")
        intent = preflight.get("intent", "prepare")
        if intent not in {"prepare", "submit", "completed"}:
            self.add("FAIL", "INVALID_PREFLIGHT_INTENT", "active_contract.preflight.intent", "Use prepare, submit or completed.")
        generation = any(a in GENERATION_ACTIONS for a in actions) and intent != "completed"
        if generation:
            for key in ("service", "model", "input_strategy"):
                if not route.get(key):
                    self.add("UNKNOWN", "ROUTE_INCOMPLETE", f"active_contract.route.{key}", "Generation route has not been selected.")
        if preflight.get("contract_id") and preflight["contract_id"] != c.get("id"):
            self.add("FAIL", "PREFLIGHT_CONTRACT_MISMATCH", "active_contract.preflight.contract_id", "Preflight belongs to a different contract.")
        bindings = preflight.get("bindings", [])
        if preflight.get("input_bindings_verified") or bindings:
            if bindings != inputs:
                self.add("FAIL", "PREFLIGHT_BINDINGS_MISMATCH", "active_contract.preflight.bindings", "Verified bindings differ from current ordered inputs.")
        if generation and not preflight.get("input_bindings_verified"):
            self.add("UNKNOWN", "PREFLIGHT_UNVERIFIED", "active_contract.preflight", "Generator bindings have not been verified.")
        quote = preflight.get("quote")
        if quote is None:
            if generation:
                self.add("UNKNOWN", "QUOTE_ABSENT", "active_contract.preflight.quote", "No current full-input quote is recorded.")
            return
        quote = self.obj(quote, "active_contract.preflight.quote")
        amount, currency = quote.get("amount"), quote.get("currency")
        if not number(amount):
            self.add("UNKNOWN", "QUOTE_PRICE_UNKNOWN", "active_contract.preflight.quote.amount", "Quote amount is unknown; zero is a valid amount.")
        elif amount < 0:
            self.add("FAIL", "INVALID_QUOTE_PRICE", "active_contract.preflight.quote.amount", "Quote amount cannot be negative.")
        if not isinstance(currency, str) or not currency.strip():
            self.add("UNKNOWN", "QUOTE_CURRENCY_UNKNOWN", "active_contract.preflight.quote.currency", "Quote currency or credit unit is unknown.")
        expected = {"contract_id": c.get("id"), "service": route.get("service"), "model": route.get("model"), "duration_sec": c.get("duration_sec"), "aspect_ratio": c.get("aspect_ratio"), "input_strategy": route.get("input_strategy"), "settings": route.get("settings", {}), "input_artifact_ids": [row.get("artifact_id") for row in inputs]}
        self.same(quote, expected, "active_contract.preflight.quote", "QUOTE_CONTRACT_MISMATCH")
        if generation:
            for key in expected:
                if key not in quote:
                    self.add("UNKNOWN", "QUOTE_INCOMPLETE", f"active_contract.preflight.quote.{key}", "Quote does not identify this part of its request.")
        limits = c.get("execution_limits", {})
        budget = limits.get("paid_budget", {}) if isinstance(limits, dict) else {}
        if isinstance(budget, dict) and number(budget.get("amount")) and number(quote.get("amount")):
            if budget.get("currency") == quote.get("currency") and budget.get("currency"):
                if quote["amount"] > budget["amount"]:
                    self.add("FAIL", "PAID_BUDGET_EXCEEDED", "active_contract.preflight.quote.amount", "This quote exceeds the current paid budget in the same unit.")
            else:
                self.add("UNKNOWN", "BUDGET_UNITS_NOT_COMPARABLE", "active_contract.preflight.quote.currency", "Do not compare credits and money without a verified conversion.")

    def temporal(self, c, duration):
        obs = self.obj(c.get("observations", {}), "active_contract.observations")
        events = {}
        for row in self.rows(obs.get("events", []), "active_contract.observations.events"):
            eid, t = row.get("id"), row.get("time_sec")
            if not isinstance(eid, str) or not eid or not number(t):
                self.add("FAIL", "INVALID_EVENT", "active_contract.observations.events", "Observed event needs an ID and finite timestamp.")
                continue
            if eid in events:
                self.add("FAIL", "DUPLICATE_EVENT", "active_contract.observations.events", "Observed event ID is ambiguous.")
            events[eid] = t
            if t < 0 or (number(duration) and t > duration):
                self.add("FAIL", "EVENT_OUTSIDE_DURATION", "active_contract.observations.events", "Observed event lies outside the current episode.")
        states = self.rows(obs.get("states", []), "active_contract.observations.states")
        valid_states = []
        for row in states:
            if not row.get("name") or not number(row.get("time_sec")) or "value" not in row:
                self.add("FAIL", "INVALID_STATE_OBSERVATION", "active_contract.observations.states", "State observation needs name, timestamp and value.")
            else:
                valid_states.append(row)
                if row["time_sec"] < 0 or (number(duration) and row["time_sec"] > duration):
                    self.add("FAIL", "STATE_OUTSIDE_DURATION", "active_contract.observations.states", "Observed state lies outside the current episode.")
        for rule in self.rows(c.get("temporal_constraints", []), "active_contract.temporal_constraints"):
            path = f"active_contract.temporal_constraints.{rule.get('id', '?')}"
            before, after = rule.get("before", []), rule.get("after", [])
            if not isinstance(before, list) or not isinstance(after, list):
                self.add("FAIL", "INVALID_TEMPORAL_RULE", path, "Before and after must be ordered event-ID arrays.")
                continue
            chain = before + ([rule["event"]] if rule.get("event") else []) + after
            if not chain or any(not isinstance(e, str) for e in chain):
                self.add("UNKNOWN", "TEMPORAL_RULE_INCOMPLETE", path, "No unambiguous event chain is supplied.")
                continue
            if any(e not in events for e in chain):
                self.add("UNKNOWN", "EVENT_EVIDENCE_ABSENT", path, "Event order cannot be checked without all observed timestamps.")
            else:
                ordered = all(events[a] <= events[b] for a, b in zip(chain, chain[1:]))
                self.add("PASS" if ordered else "FAIL", "TEMPORAL_ORDER", path, "Explicit event timestamps follow the required order." if ordered else "Explicit event timestamps contradict the required order.")
            event = rule.get("event")
            if not isinstance(event, str) or event not in events:
                continue
            pivot = events[event]
            state = rule.get("state")
            if state is not None:
                state = self.obj(state, path + ".state")
                samples = [s for s in valid_states if s["name"] == state.get("name")]
                persistence_end = rule.get("persistence")
                end_time = events.get(persistence_end.get("until_event")) if isinstance(persistence_end, dict) else None
                for side in ("before", "after"):
                    if side not in state:
                        continue
                    observed = [s for s in samples if (s["time_sec"] < pivot if side == "before" else s["time_sec"] >= pivot)]
                    if side == "after" and end_time is not None:
                        observed = [s for s in observed if s["time_sec"] <= end_time]
                    if not observed:
                        self.add("UNKNOWN", "STATE_EVIDENCE_ABSENT", path + ".state." + side, "No explicit state observations cover this side of the event.")
                    else:
                        matches = all(s["value"] == state[side] for s in observed)
                        self.add("PASS" if matches else "FAIL", "TEMPORAL_STATE", path + ".state." + side, "Supplied state samples agree with the transition." if matches else "Supplied state samples contradict the transition.")
            persistence = rule.get("persistence")
            if persistence is not None:
                persistence = self.obj(persistence, path + ".persistence")
                end = events.get(persistence.get("until_event"))
                name = persistence.get("name") or (state or {}).get("name")
                if end is None or end < pivot or not name or "value" not in persistence:
                    self.add("UNKNOWN" if end is None else "FAIL", "PERSISTENCE_INCOMPLETE", path, "Persistence needs a known end event, state name and value.")
                    continue
                samples = [s for s in valid_states if s["name"] == name and pivot <= s["time_sec"] <= end]
                if not samples:
                    self.add("UNKNOWN", "PERSISTENCE_EVIDENCE_ABSENT", path, "No explicit state samples cover persistence.")
                else:
                    matches = all(s["value"] == persistence["value"] for s in samples)
                    self.add("PASS" if matches else "FAIL", "STATE_PERSISTENCE", path, "Supplied samples preserve the required state." if matches else "Supplied samples lose the required persistent state.")

    def evidence(self, c, artifacts):
        for row in self.rows(c.get("evidence_findings", []), "active_contract.evidence_findings") + self.rows(c.get("action_checkpoints", []), "active_contract.action_checkpoints"):
            status = row.get("status", "unknown")
            if status not in {"pass", "fail", "unknown"}:
                self.add("FAIL", "INVALID_EVIDENCE_STATUS", "active_contract.evidence_findings", "Use pass, fail or unknown.")
            elif status == "unknown" or not isinstance(row.get("evidence_refs"), list) or not row["evidence_refs"] or not all(isinstance(ref, str) and ref.strip() for ref in row["evidence_refs"]):
                self.add("UNKNOWN", "EVIDENCE_NOT_ESTABLISHED", "active_contract.evidence_findings", "Unverified or unsupported finding remains unknown.")
            else:
                self.add("FAIL" if status == "fail" else "PASS", "EXPLICIT_FINDING", "active_contract.evidence_findings", "Recorded explicit finding: " + str(row.get("id", "unnamed")))
        summary = self.obj(c.get("qa_summary", {}), "active_contract.qa_summary")
        reports = self.rows(c.get("reports", []), "active_contract.reports")
        # IDs must identify the same report AND artifact before a summary can contradict it.
        for report in reports:
            if summary.get("report_id") and summary.get("artifact_id") and report.get("id") == summary["report_id"] and report.get("artifact_id") == summary["artifact_id"]:
                if report.get("status") and summary.get("status") != report["status"]:
                    self.add("FAIL", "QA_SUMMARY_STALE", "active_contract.qa_summary", "Summary contradicts its explicitly identified report and artifact.")
        selection = self.obj(c.get("user_selection", {}), "active_contract.user_selection")
        if selection.get("artifact_id") and selection["artifact_id"] not in artifacts:
            self.add("FAIL", "SELECTED_ARTIFACT_MISSING", "active_contract.user_selection", "User-selected artifact is absent from the current artifacts.")
        if selection.get("accepted") is True and not selection.get("evidence_ref"):
            self.add("UNKNOWN", "USER_ACCEPTANCE_UNVERIFIED", "active_contract.user_selection", "User acceptance needs its own evidence; QA does not establish acceptance.")

    def limits(self, c):
        limits = self.obj(c.get("execution_limits", {}), "active_contract.execution_limits")
        for key in ("max_runs", "runs_started", "automatic_local_repair_cap"):
            value = limits.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                self.add("UNKNOWN" if value is None else "FAIL", "INVALID_EXECUTION_LIMIT", f"active_contract.execution_limits.{key}", "Expected an explicit nonnegative integer.")
        cap, runs = limits.get("max_runs"), limits.get("runs_started")
        if all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in (cap, runs)):
            self.execution_capacity = {"max_runs": cap, "runs_started": runs, "remaining_paid_runs": max(0, cap - runs)}
            if runs > cap:
                self.add("FAIL", "RUN_LIMIT_EXCEEDED", "active_contract.execution_limits", "Started runs exceed the selected maximum.")
        preflight = c.get("preflight", {})
        if isinstance(preflight, dict) and preflight.get("intent", "prepare") == "submit":
            remaining = self.execution_capacity["remaining_paid_runs"]
            if remaining is None:
                self.add("UNKNOWN", "SUBMISSION_CAPACITY_UNKNOWN", "active_contract.execution_limits", "Submission capacity has not been established.")
            elif remaining == 0:
                self.add("FAIL", "SUBMISSION_RUN_CAPACITY_EXHAUSTED", "active_contract.execution_limits", "Explicit submission has no remaining paid run capacity.")
        minutes = limits.get("local_time_budget_minutes")
        if minutes is not None and (not number(minutes) or minutes < 0):
            self.add("FAIL", "INVALID_TIME_BUDGET", "active_contract.execution_limits.local_time_budget_minutes", "Time budget must be nonnegative.")
        budget = self.obj(limits.get("paid_budget", {}), "active_contract.execution_limits.paid_budget")
        amount = budget.get("amount")
        if amount is not None and (not number(amount) or amount < 0):
            self.add("FAIL", "INVALID_PAID_BUDGET", "active_contract.execution_limits.paid_budget.amount", "Paid budget must be nonnegative.")
        if amount is not None and not budget.get("currency"):
            self.add("UNKNOWN", "BUDGET_CURRENCY_ABSENT", "active_contract.execution_limits.paid_budget.currency", "Currency or credit unit is required for a monetary amount.")

    def result(self, cid):
        counts = {s.lower(): sum(f["status"] == s for f in self.findings) for s in ("PASS", "FAIL", "UNKNOWN")}
        status = "FAIL" if counts["fail"] else "UNKNOWN" if counts["unknown"] else "PASS"
        return {"status": status, "contract_id": cid, "scope": "contract_consistency_and_supplied_explicit_evidence_only", "visual_or_audio_quality_inferred": False, "execution_capacity": self.execution_capacity, "counts": counts, "findings": self.findings}


def validate_scene(scene, project_root):
    """Return a JSON-serializable report without mutating scene or its files."""
    if not isinstance(scene, dict):
        raise ValueError("Scene JSON must contain an object.")
    return Validator(scene, project_root).run()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        scene = json.loads(args.scene.read_text(encoding="utf-8"))
        report = validate_scene(scene, args.project_root)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"PASS": 0, "FAIL": 1, "UNKNOWN": 3}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
