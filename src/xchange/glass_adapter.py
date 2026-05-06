from __future__ import annotations

from typing import Any

from xchange.grid_substantiation import normalize_grid_substantiation_evidence


def map_glass_bridge_to_ingest(
    bridge: dict[str, Any],
    *,
    student_id: str,
    reward_id: str | None = None,
    contract_satisfied: bool = False,
    ready_for_payment: bool = False,
    student_ack: bool = False,
    request_review: bool = False,
    failure: dict[str, Any] | None = None,
    grid_substantiation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session_id = bridge.get("session_id")
    if not session_id:
        raise ValueError("bridge must contain session_id")
    if not student_id or not isinstance(student_id, str):
        raise ValueError("student_id must be a non-empty string")
    if reward_id is not None and (not reward_id or not isinstance(reward_id, str)):
        raise ValueError("reward_id must be a non-empty string when provided")

    result: dict[str, Any] = {
        "session_id": str(session_id),
        "student_id": student_id,
        "_glass_bridge": bridge,
    }
    if reward_id:
        result["reward_id"] = reward_id
    if contract_satisfied:
        result["contract_satisfied"] = True
    if ready_for_payment:
        result["ready_for_payment"] = True
    if student_ack:
        result["student_ack"] = True
    if request_review:
        result["request_review"] = True
    if failure is not None:
        result["failure"] = failure
    if grid_substantiation is not None:
        result["_grid_substantiation"] = normalize_grid_substantiation_evidence(
            grid_substantiation
        )
    return result
