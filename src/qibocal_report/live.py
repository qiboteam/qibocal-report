"""Debounced, incremental report updates while a WebSocket is subscribed."""

import asyncio
import json
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from qibocal_report.archive import resolve_report_dir
from qibocal_report.generator import (
    _generate_qibocal_protocols,
    load_cached_protocols,
    report_generation_lock,
    sort_protocols_by_execution_order,
    write_protocol_cache,
)
from qibocal_report.live_inputs import (
    metadata_inputs,
    protocol_inputs,
    write_input_cache,
)
from qibocal_report.logger import log_info, log_warning
from qibocal_report.models import ProtocolDetail
from qibocal_report.notes import attach_protocol_notes
from qibocal_report.scanner import get_report_detail, invalidate_report_cache

LIVE_POLL_INTERVAL = 1.0


def cached_inputs(report_dir: Path, current: dict) -> dict:
    """Use saved fingerprints, or adopt existing legacy caches as a baseline."""
    with report_generation_lock(report_dir):
        path = report_dir / "report" / ".live-inputs.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid live input cache")
            return data
        baseline = {
            p.id: current.get(p.id) if p.status == "success" else None
            for p in load_cached_protocols(report_dir)
        }
        write_input_cache(report_dir, baseline)
        return baseline


def refresh_live_protocols(
    report_dir: Path, current: dict, previous: dict
) -> tuple[list[ProtocolDetail], list[str]]:
    """Generate changed tasks only, merging with unaffected cached outputs."""
    with report_generation_lock(report_dir):
        known = cached_inputs(report_dir, previous)
        cached = {p.id: p for p in load_cached_protocols(report_dir)}
        changed = [
            key
            for key in current
            if current[key] != previous.get(key) or key not in cached
        ]
        generate = [
            key
            for key in changed
            if current[key] != known.get(key) or key not in cached
        ]
        removed = [key for key in previous if key not in current]
        failures = {}
        if generate:
            protocols, error = _generate_qibocal_protocols(report_dir, generate)
            if protocols is None:
                raise RuntimeError(error or "Live plot generation failed")
            generated_ids = {p.id for p in protocols}
            if generated_ids != set(generate):
                raise RuntimeError(
                    "Live plot generation returned incomplete task outputs"
                )
            for protocol in protocols:
                if protocol.status == "success":
                    cached[protocol.id] = protocol
                    known[protocol.id] = current[protocol.id]
                else:
                    old = cached.get(protocol.id)
                    if old is not None:
                        failures[protocol.id] = old.model_copy(
                            update={
                                "status": "error",
                                "error": protocol.error
                                or "Live plot generation failed",
                                "error_code": protocol.error_code,
                            }
                        )
                    else:
                        cached[protocol.id] = protocol
                        failures[protocol.id] = protocol
        for key in removed:
            cached.pop(key, None)
            known.pop(key, None)
        if generate or removed:
            write_protocol_cache(
                report_dir,
                sort_protocols_by_execution_order(list(cached.values()), report_dir),
            )
            write_input_cache(report_dir, known)
        return attach_protocol_notes(
            report_dir, [failures.get(key, cached[key]) for key in changed]
        ), removed


def live_initial_state(
    report_dir: Path, current: dict
) -> tuple[list[ProtocolDetail], dict]:
    """Read outputs and their matching fingerprints under the same lock."""
    with report_generation_lock(report_dir):
        return load_cached_protocols(report_dir), cached_inputs(report_dir, current)


async def handle_live_websocket(
    websocket: WebSocket,
    report_id: str,
    root_dir: Path,
    authorized: Callable[[], bool],
) -> None:
    """Watch until disconnect; wait for two identical snapshots before plotting."""
    if not authorized():
        await websocket.close(code=1008)
        return
    try:
        target = resolve_report_dir(root_dir, report_id).resolve()
        if not target.is_relative_to(root_dir.resolve()) or (
            target == root_dir.resolve() and report_id != target.name
        ):
            raise HTTPException(404, "Report not found")
    except HTTPException:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    log_info(f"Live report subscription started for '{report_id}'")

    async def watch():
        previous = None
        previous_meta = None
        previous_notes = None
        emitted: dict[str, ProtocolDetail] = {}
        candidate = None
        last_error = None
        await websocket.send_json({"type": "live", "active": True})
        while True:
            if not authorized():
                await websocket.send_json(
                    {"type": "error", "message": "Live mode requires editor access."}
                )
                await websocket.close(code=1008)
                return
            try:
                if not target.is_dir():
                    await websocket.send_json(
                        {"type": "error", "message": f"Report '{report_id}' not found"}
                    )
                    await websocket.close()
                    return
                current = await asyncio.to_thread(protocol_inputs, target)
                meta = await asyncio.to_thread(metadata_inputs, target)
                notes = [entry for entry in meta if entry[0].endswith("notes.json")]
                if previous is None:
                    protocols, previous = await asyncio.to_thread(
                        live_initial_state, target, current
                    )
                    emitted = {p.id: p for p in protocols}
                    await websocket.send_json(
                        {
                            "type": "snapshot",
                            "protocols": [p.model_dump(mode="json") for p in protocols],
                        }
                    )
                snapshot = (current, meta)
                if snapshot == candidate and (
                    current != previous or meta != previous_meta
                ):
                    outputs, removed = await asyncio.to_thread(
                        refresh_live_protocols, target, current, previous
                    )
                    if previous_notes is not None and notes != previous_notes:
                        # Comment-only updates do not require plotting.
                        updated = {
                            key: protocol for key, protocol in emitted.items()
                            if key not in removed
                        }
                        await asyncio.to_thread(
                            attach_protocol_notes, target, list(updated.values())
                        )
                        updated.update({p.id: p for p in outputs})
                        outputs = list(updated.values())
                    invalidate_report_cache()
                    detail = await asyncio.to_thread(
                        get_report_detail, root_dir, report_id
                    )
                    if detail:
                        await websocket.send_json(
                            {
                                "type": "metadata",
                                "report": detail.model_dump(mode="json"),
                            }
                        )
                    if outputs or removed:
                        await websocket.send_json(
                            {
                                "type": "update",
                                "protocols": [
                                    p.model_dump(mode="json") for p in outputs
                                ],
                                "removed": removed,
                            }
                        )
                        emitted.update({p.id: p for p in outputs})
                        for key in removed:
                            emitted.pop(key, None)
                    previous, previous_meta = current, meta
                    previous_notes = notes
                    last_error = None
                candidate = snapshot
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                message = f"Live update failed: {error}"
                if message != last_error:
                    log_warning(message)
                    await websocket.send_json({"type": "error", "message": message})
                    last_error = message
                # Retry unfinished writes, but not expensive generation failures
                # until their inputs change again.
                if isinstance(error, RuntimeError) and candidate is not None:
                    previous, previous_meta = candidate
            await asyncio.sleep(LIVE_POLL_INTERVAL)

    task = asyncio.create_task(watch())

    async def receive():
        while True:
            if await websocket.receive_text() == "ping":
                await websocket.send_text("pong")

    receiver = asyncio.create_task(receive())
    try:
        done, _ = await asyncio.wait(
            (task, receiver), return_when=asyncio.FIRST_COMPLETED
        )
        for completed in done:
            completed.result()
    except WebSocketDisconnect:
        log_info(f"Live report subscription stopped for '{report_id}'")
    except (OSError, RuntimeError) as error:
        log_warning(f"Live session ended for '{report_id}': {error}")
    finally:
        for pending in (task, receiver):
            pending.cancel()
        with suppress(asyncio.CancelledError):
            await asyncio.gather(task, receiver, return_exceptions=True)
