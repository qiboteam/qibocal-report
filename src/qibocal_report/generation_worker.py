"""Fresh-process entrypoint for Qibocal plot generation."""

import json
import sys
from pathlib import Path

from qibocal_report.generator import _generate_qibocal_protocols_native


def _json_default(value):
    return value.tolist() if hasattr(value, "tolist") else str(value)


def main() -> None:
    report_dir, result_path = (Path(argument) for argument in sys.argv[1:])
    protocols, error = _generate_qibocal_protocols_native(report_dir)
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
