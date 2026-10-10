"""WebSocket streaming session handler for live report progress."""

import asyncio
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

from qibocal_report.generator import (
    get_report_protocols,
    has_cached_report,
    load_cached_protocols,
)
from qibocal_report.logger import (
    log_error,
    log_info,
    log_success,
    log_warning,
)
from qibocal_report.notes import NotesError
from qibocal_report.scanner import get_report_detail, scan_reports


async def handle_report_websocket(
    websocket: WebSocket, report_id: str, root_dir: Path
) -> None:
    """Stream report metadata, progress, and protocol outputs over WebSocket."""
    await websocket.accept()
    log_info(f"WebSocket client connected for report: '{report_id}'")

    target_dir = root_dir / report_id
    if not target_dir.is_dir():
        for r in scan_reports(root_dir):
            if r.id == report_id:
                target_dir = Path(r.path)
                break

    if not target_dir.is_dir():
        log_error(f"Report '{report_id}' not found for WebSocket client")
        await websocket.send_json(
            {"type": "error", "message": f"Report '{report_id}' not found"}
        )
        await websocket.close()
        return

    try:
        # Step 1: Send metadata immediately
        detail = get_report_detail(root_dir, report_id)
        if detail:
            await websocket.send_json(
                {"type": "metadata", "report": detail.model_dump(mode="json")}
            )

        # Step 2: Stream protocols
        if has_cached_report(target_dir):
            log_info(f"Report '{report_id}' has cached artifacts. Loading from disk...")
            await websocket.send_json(
                {"type": "status", "message": "Loading pre-cached report artifacts..."}
            )
            protocols = load_cached_protocols(target_dir)
            await websocket.send_json(
                {
                    "type": "ready",
                    "protocols": [p.model_dump(mode="json") for p in protocols],
                }
            )
            log_success(
                f"Dispatched {len(protocols)} pre-cached protocol(s) over "
                f"WebSocket for '{report_id}'."
            )
        else:
            log_info(f"Report '{report_id}' needs plot generation. Starting worker...")
            await websocket.send_json(
                {
                    "type": "status",
                    "message": (
                        "Initializing protocol evaluation and plot generation..."
                    ),
                }
            )

            loop = asyncio.get_running_loop()

            def sync_progress(step: int, total: int, proto_name: str):
                try:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json(
                            {
                                "type": "progress",
                                "step": step,
                                "total": total,
                                "protocol": proto_name,
                                "message": (
                                    f"Plotting protocol {proto_name} "
                                    f"({step}/{total})..."
                                ),
                            }
                        ),
                        loop,
                    )
                except (RuntimeError, OSError) as err:
                    log_warning(f"Could not send WebSocket progress: {err}")

            protocols = await loop.run_in_executor(
                None,
                lambda: get_report_protocols(
                    target_dir, progress_callback=sync_progress
                ),
            )

            await websocket.send_json(
                {
                    "type": "ready",
                    "protocols": [p.model_dump(mode="json") for p in protocols],
                }
            )
            log_success(
                f"Dispatched {len(protocols)} generated protocol(s) over "
                f"WebSocket for '{report_id}'."
            )

        # Keep-alive loop
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        log_info(f"WebSocket client disconnected for report: '{report_id}'")
    except NotesError as err:
        log_warning(f"Could not load notes for '{report_id}': {err}")
        await websocket.send_json({"type": "error", "message": str(err)})
        await websocket.close()
    except (RuntimeError, OSError) as err:
        log_warning(f"WebSocket session ended for '{report_id}': {err}")
