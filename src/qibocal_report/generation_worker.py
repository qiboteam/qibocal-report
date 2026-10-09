"""Fresh-process entrypoint for Qibocal plot generation."""

import json
import sys
from pathlib import Path

from qibocal_report.generator import _generate_qibocal_protocols_native


def _json_default(value):
    return value.tolist() if hasattr(value, "tolist") else str(value)


def main() -> None:
    report_dir, result_path = (Path(argument) for argument in sys.argv[1:3])
    protocol_ids = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    protocols, error = (
        _generate_qibocal_protocols_native(report_dir)
        if protocol_ids is None
        else _generate_qibocal_protocols_native(report_dir, protocol_ids)
    )
    payload = {
        "protocols": [protocol.model_dump() for protocol in protocols]
        if protocols is not None
        else None,
        "error": error,
        "error_code": getattr(error, "error_code", None),
    }
    result_path.write_text(json.dumps(payload, default=_json_default), encoding="utf-8")


if __name__ == "__main__":
    main()
