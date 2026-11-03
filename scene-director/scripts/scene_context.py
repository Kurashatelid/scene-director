#!/usr/bin/env python3
"""Print the current contract without history; read-only, not QA or authorization.

Usage: python3 scripts/scene_context.py SCENE_JSON
Exit: 0 current contract returned, 3 migration required, 2 input error.
The current contract is retained verbatim, including unknown extension fields.
Root job logs, legacy mirrors and history remain available in the source file.
"""

import argparse
import json
from pathlib import Path


def current_context(scene, source):
    if not isinstance(scene, dict):
        raise ValueError("Scene must be a JSON object.")
    result = {
        "source": str(source),
        "schema_version": scene.get("schema_version"),
        "scene_id": scene.get("scene_id"),
        "title": scene.get("title"),
        "stage": scene.get("stage"),
        "scene_status": scene.get("status"),
        "is_authorization": False,
    }
    contract = scene.get("active_contract")
    if scene.get("schema_version") != 3 or not isinstance(contract, dict) or not contract:
        result.update(status="MIGRATION_REQUIRED", active_contract=None)
        return result, 3
    result.update(
        status="CURRENT_SNAPSHOT",
        active_contract=contract,
        supplemental_fields=sorted(k for k in scene if k not in result and k not in {"active_contract", "status"}),
    )
    return result, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    args = parser.parse_args()
    try:
        source = args.scene.resolve()
        result, code = current_context(json.loads(source.read_text(encoding="utf-8")), source)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "INPUT_ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
