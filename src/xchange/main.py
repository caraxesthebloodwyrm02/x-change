from __future__ import annotations

import hashlib
import json
import math
import os
import time
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from xchange.domain import (
    ConstraintConfig,
    ExchangeRequest,
    InsightTier,
    RewardToken,
    compute_rarity_score,
    evaluate_exchange_request,
)
from xchange.glass_adapter import map_glass_bridge_to_ingest
from xchange.nudge import suggest_path_semantics
from xchange.storage import (
    FailureSnapshot,
    acknowledge_reward,
    create_nudge,
    create_reward_draft,
    get_outcome_summary,
    get_reward_state,
    ingest_glass_session,
    insert_support_signal,
    issue_reward_token,
    latest_failure_for_student,
    list_exchange_requests,
    list_support_signals,
    open_db,
    process_stripe_payment_intent_succeeded,
    resolve_support_signal,
    store_exchange_request,
)
from xchange.stripe_sig import verify_stripe_signature


class BodyTooLargeError(Exception):
    """Raised when a request body exceeds the configured size cap."""


_RATE_LIMIT_BUCKETS: dict[tuple[str, str], list[float]] = {}
_RATE_LIMIT_LOCK = Lock()


def _json_response(
    handler: BaseHTTPRequestHandler,
    *,
    status: int,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for name, value in (headers or {}).items():
        handler.send_header(name, value)
    handler.end_headers()
    handler.wfile.write(body)


def _html_response(
    handler: BaseHTTPRequestHandler,
    *,
    status: int,
    html: str,
    headers: dict[str, str] | None = None,
) -> None:
    body = html.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for name, value in (headers or {}).items():
        handler.send_header(name, value)
    handler.end_headers()
    handler.wfile.write(body)


def _max_body_bytes() -> int:
    """Return the maximum permitted request body size in bytes.

    Defaults to 65536 (64 KB). Override with the ``XCHANGE_MAX_BODY_BYTES``
    environment variable.
    """
    try:
        return max(1, int(os.environ.get("XCHANGE_MAX_BODY_BYTES", "65536")))
    except ValueError:
        return 65536


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    """Read and JSON-decode the request body.

    Raises:
        BodyTooLargeError: Content-Length header exceeds ``XCHANGE_MAX_BODY_BYTES``.
        ValueError: Body is not valid UTF-8 JSON.
    """
    max_bytes = _max_body_bytes()
    length_str = handler.headers.get("Content-Length")
    if length_str is not None:
        try:
            length = int(length_str)
        except ValueError:
            length = 0
        if length > max_bytes:
            raise BodyTooLargeError(
                f"body exceeds limit: {length} bytes (max {max_bytes})"
            )
    else:
        length = 0
    # Always cap the actual read — guards against absent / spoofed Content-Length.
    raw = handler.rfile.read(min(length, max_bytes)) if length > 0 else b"{}"
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON: {e}") from e


def _parse_body(handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
    """Size-guard, read, and JSON-decode the request body.

    On success returns the parsed dict.  On error writes the appropriate HTTP
    response (413 or 400) and returns ``None`` so the caller can ``return``
    immediately without extra error-handling boilerplate.
    """
    try:
        return _read_json_body(handler)
    except BodyTooLargeError as e:
        _json_response(
            handler,
            status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            payload={"error": "body_too_large", "detail": str(e)},
        )
        return None
    except ValueError as e:
        _json_response(
            handler,
            status=HTTPStatus.BAD_REQUEST,
            payload={"error": str(e)},
        )
        return None


def _require_ingest_token(handler: BaseHTTPRequestHandler) -> bool:
    token = os.environ.get("XCHANGE_INGEST_TOKEN")
    if not token:
        return False
    auth = handler.headers.get("Authorization", "")
    expected = f"Bearer {token}"
    if auth == expected:
        return True
    x_token = handler.headers.get("X-Ingest-Token")
    if x_token and x_token == token:
        return True
    return False


def _rate_limit_settings() -> tuple[int, float]:
    try:
        limit = int(os.environ.get("XCHANGE_RATE_LIMIT_REQUESTS", "60"))
    except ValueError:
        limit = 60
    try:
        window_seconds = float(
            os.environ.get("XCHANGE_RATE_LIMIT_WINDOW_SECONDS", "60")
        )
    except ValueError:
        window_seconds = 60
    return limit, window_seconds


def _operator_rate_limit_key() -> str:
    token = os.environ.get("XCHANGE_INGEST_TOKEN", "")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def _check_rate_limit(*, route_class: str, key: str) -> tuple[bool, int]:
    limit, window_seconds = _rate_limit_settings()
    if limit <= 0 or window_seconds <= 0:
        return True, 0

    now = time.monotonic()
    bucket_key = (route_class, key)
    with _RATE_LIMIT_LOCK:
        bucket = _RATE_LIMIT_BUCKETS.setdefault(bucket_key, [])
        bucket[:] = [seen_at for seen_at in bucket if now - seen_at < window_seconds]
        if len(bucket) >= limit:
            retry_after = max(1, math.ceil(window_seconds - (now - bucket[0])))
            return False, retry_after
        bucket.append(now)
    return True, 0


def _enforce_operator_rate_limit(handler: BaseHTTPRequestHandler) -> bool:
    allowed, retry_after = _check_rate_limit(
        route_class="operator",
        key=_operator_rate_limit_key(),
    )
    if allowed:
        return True
    _json_response(
        handler,
        status=HTTPStatus.TOO_MANY_REQUESTS,
        payload={"error": "rate_limited", "retry_after_seconds": retry_after},
        headers={"Retry-After": str(retry_after)},
    )
    return False


def _require_operator_access(handler: BaseHTTPRequestHandler) -> bool:
    if not _require_ingest_token(handler):
        _json_response(
            handler, status=HTTPStatus.UNAUTHORIZED, payload={"error": "unauthorized"}
        )
        return False
    return _enforce_operator_rate_limit(handler)


def _reset_rate_limit_for_tests() -> None:
    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_BUCKETS.clear()


def _get_db_path() -> str:
    return os.environ.get("XCHANGE_DB_PATH", "xchange.sqlite")


def _stable_json_sha256(value: Any) -> str:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except TypeError:
        raw = json.dumps(str(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _redact_evidence_payload(payload: Any) -> dict[str, Any]:
    """Summarize evidence payloads for collaborator-safe read exposure."""
    if payload is None:
        return {"redacted": True, "sha256": _stable_json_sha256(None), "keys": []}
    if isinstance(payload, dict):
        keys = sorted(str(k) for k in payload.keys())
        return {"redacted": True, "sha256": _stable_json_sha256(payload), "keys": keys}
    if isinstance(payload, list):
        return {
            "redacted": True,
            "sha256": _stable_json_sha256(payload),
            "keys": [],
            "list_len": len(payload),
        }
    return {"redacted": True, "sha256": _stable_json_sha256(payload), "keys": []}


def _sanitize_reward_state_for_readonly_view(state: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive raw payloads from reward state JSON responses."""
    safe = dict(state)

    evidence = safe.get("evidence")
    if isinstance(evidence, list):
        sanitized: list[dict[str, Any]] = []
        for item in evidence:
            if not isinstance(item, dict):
                continue
            sanitized_item = dict(item)
            sanitized_item["payload"] = _redact_evidence_payload(item.get("payload"))
            sanitized.append(sanitized_item)
        safe["evidence"] = sanitized

    # Legacy mirror includes last_payload_json (full Stripe payload / ingest payload) — never expose.
    safe.pop("legacy_rewards_row", None)
    return safe


def _handle_readonly_viewer_route(handler: BaseHTTPRequestHandler) -> None:
    """Serve the read-only trust surface viewer HTML.

    Requires operator access and supports optional ?reward_id=<id> filtering.
    """
    if not _require_operator_access(handler):
        return

    parsed = urlparse(handler.path)
    from urllib.parse import parse_qs

    qs = parse_qs(parsed.query)
    reward_id = (qs.get("reward_id", [""])[0] or "").strip()

    with open_db(_get_db_path()) as conn:
        reward_state = None
        if reward_id:
            reward_state = get_reward_state(conn, reward_id=reward_id)
            if not reward_state:
                _json_response(
                    handler,
                    status=HTTPStatus.NOT_FOUND,
                    payload={"error": "reward_not_found"},
                )
                return
        summary = get_outcome_summary(conn)
        exchange_rows = list_exchange_requests(
            conn=conn,
            reward_id=reward_id or None,
            limit=20,
        )

    badge = '<span class="badge">READ-ONLY</span>'

    last_transition_reason = "No transition log available"
    last_transition_at = "n/a"
    evidence_count = 0
    current_lifecycle = "n/a"
    current_outcome = "n/a"
    token_status = "n/a"
    token_id_preview = "n/a"

    reward_panel = ""
    if reward_state:
        notes_obj = reward_state.get("notes")
        if isinstance(notes_obj, dict):
            log = notes_obj.get("transition_log")
            if isinstance(log, list) and log:
                last = log[-1]
                if isinstance(last, dict):
                    last_transition_at = str(last.get("at", "n/a"))
                    note_items = last.get("notes")
                    if isinstance(note_items, list) and note_items:
                        last_transition_reason = "; ".join(str(n) for n in note_items)

        evidence = reward_state.get("evidence")
        if isinstance(evidence, list):
            evidence_count = len(evidence)

        current_lifecycle = str(reward_state.get("state", "n/a"))
        current_outcome = str(reward_state.get("outcome_state", "n/a"))
        reward_token = reward_state.get("reward_token")
        if isinstance(reward_token, dict):
            token_status = "Issued"
            token_id = str(reward_token.get("id", "")).strip()
            token_id_preview = token_id[:16] + "..." if len(token_id) > 16 else token_id or "present"
        else:
            token_status = "Not issued"
            token_id_preview = "none"

        reward_panel = f"""
        <section class="panel">
          <h2>Reward Details</h2>
          <dl>
            <dt>Reward ID</dt><dd>{escape(str(reward_state.get("reward_id", "")))}</dd>
            <dt>Student ID</dt><dd>{escape(str(reward_state.get("student_id", "")))}</dd>
            <dt>Policy Lifecycle</dt><dd>{escape(current_lifecycle)}</dd>
            <dt>Student Outcome</dt><dd>{escape(current_outcome)}</dd>
            <dt>Last Updated</dt><dd>{escape(str(reward_state.get("updated_at", "")))}</dd>
          </dl>
        </section>
        """

    summary_states = summary.get("by_state", {})
    state_chips = ""
    if isinstance(summary_states, dict) and summary_states:
        state_chips = "".join(
            f'<span class="chip">{escape(str(name))}: {escape(str(count))}</span>'
            for name, count in sorted(summary_states.items())
        )
    else:
        state_chips = '<span class="chip">No rewards yet</span>'

    exchange_items = "".join(
        (
            "<tr>"
            f"<td>{escape(str(row.get('request_id', '')))}</td>"
            f"<td>{escape(str(row.get('reward_id', '')))}</td>"
            f"<td>{escape(str(row.get('student_id', '')))}</td>"
            f"<td>{'yes' if bool(row.get('approved')) else 'no'}</td>"
            f"<td>{escape(str(row.get('created_at', '')))}</td>"
            "</tr>"
        )
        for row in exchange_rows
    )
    if not exchange_items:
        exchange_items = (
            '<tr><td colspan="5">No exchange requests found for this scope.</td></tr>'
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>x-change Read-Only Viewer</title>
    <style>
        :root {{ --bg: #f6f8f9; --card: #ffffff; --ink: #17212b; --mute: #607080; --line: #d7e0e8; --accent: #0b6b88; }}
        body {{ margin: 0; font-family: "Source Sans 3", "IBM Plex Sans", sans-serif; background: linear-gradient(135deg, #eef4f7, #f7fafc); color: var(--ink); }}
        .wrap {{ max-width: 1080px; margin: 0 auto; padding: 24px; }}
        h1 {{ margin: 0 0 8px; font-size: 32px; letter-spacing: 0.2px; }}
        p {{ margin: 0; color: var(--mute); }}
        .badge {{ display: inline-block; margin-left: 8px; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #fff; background: var(--accent); }}
        .grid {{ display: grid; gap: 14px; margin-top: 18px; }}
        .panel {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 14px; }}
        .panel h2 {{ margin: 0 0 10px; font-size: 18px; }}
        dl {{ display: grid; grid-template-columns: minmax(220px, 280px) 1fr; gap: 6px 10px; margin: 0; }}
        dt {{ color: var(--mute); }}
        dd {{ margin: 0; font-weight: 600; }}
        .chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .chip {{ border: 1px solid var(--line); background: #f2f6f8; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 700; color: #264253; }}
        .highlight {{ border-left: 4px solid var(--accent); background: #f6fbfd; }}
        .micro {{ color: var(--mute); font-size: 12px; line-height: 1.5; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; border-top: 1px solid var(--line); padding: 8px 6px; font-size: 14px; }}
        th {{ color: var(--mute); font-weight: 600; }}
    </style>
</head>
<body>
    <main class="wrap">
        <h1>x-change Trust Surface Viewer {badge}</h1>
        <p>Server-rendered operator view. This interface does not submit write requests.</p>
        <div class="grid">
            <section class="panel highlight">
                <h2>Trust Signal</h2>
                <dl>
                    <dt>Policy Lifecycle</dt><dd>{escape(current_lifecycle)}</dd>
                    <dt>Student Outcome</dt><dd>{escape(current_outcome)}</dd>
                    <dt>Last Transition Notes</dt><dd>{escape(last_transition_reason)}</dd>
                    <dt>Last Transition Time</dt><dd>{escape(last_transition_at)}</dd>
                    <dt>Evidence Count</dt><dd>{escape(str(evidence_count))}</dd>
                    <dt>Reward Token Issuance</dt><dd>{escape(token_status)}</dd>
                    <dt>Reward Token ID</dt><dd>{escape(token_id_preview)}</dd>
                </dl>
            </section>
            {reward_panel}
            <section class="panel">
                <h2>Outcomes Snapshot</h2>
                <dl>
                    <dt>Total Rewards</dt><dd>{escape(str(summary.get("total_rewards", 0)))}</dd>
                    <dt>Unique Students</dt><dd>{escape(str(summary.get("student_count", 0)))}</dd>
                    <dt>Rewards by Lifecycle</dt><dd><div class="chips">{state_chips}</div></dd>
                </dl>
            </section>
            <section class="panel">
                <h2>Exchange Requests</h2>
                <table>
                    <thead>
                        <tr><th>Request ID</th><th>Reward ID</th><th>Student ID</th><th>Approved</th><th>Created At</th></tr>
                    </thead>
                    <tbody>{exchange_items}</tbody>
                </table>
            </section>
            <section class="panel micro">
                <h2>Field Guide</h2>
                <p><strong>Policy Lifecycle</strong>: where the reward sits in the policy progression.</p>
                <p><strong>Student Outcome</strong>: student-side completion/acknowledgement state.</p>
                <p><strong>Reward Token Issuance</strong>: whether a reward token has been minted for this reward.</p>
                <p><strong>Approved</strong>: request passed configured exchange constraints.</p>
            </section>
        </div>
    </main>
</body>
</html>
"""
    _html_response(handler, status=HTTPStatus.OK, html=html)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "x-change/0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/v0/viewer":
            _handle_readonly_viewer_route(self)
            return

        if parsed.path.startswith("/v0/state/reward/"):
            if not _require_operator_access(self):
                return
            reward_id = parsed.path.split("/v0/state/reward/")[1]
            reward_id = reward_id.split("?")[0].strip() or reward_id
            with open_db(_get_db_path()) as conn:
                state = get_reward_state(conn, reward_id=reward_id)
            if not state:
                _json_response(
                    self,
                    status=HTTPStatus.NOT_FOUND,
                    payload={"error": "reward_not_found"},
                )
                return
            _json_response(
                self,
                status=HTTPStatus.OK,
                payload=_sanitize_reward_state_for_readonly_view(state),
            )
            return

        if parsed.path == "/v0/support-signals":
            self._handle_list_support_signals()
            return

        if parsed.path == "/v0/outcomes/summary":
            self._handle_outcome_summary()
            return

        if parsed.path == "/v0/exchange/requests":
            self._handle_list_exchange_requests()
            return

        _json_response(
            self, status=HTTPStatus.NOT_FOUND, payload={"error": "not_found"}
        )

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/v0/ingest/glass-session":
            self._handle_ingest_glass_session()
            return
        if parsed.path == "/v0/ingest/glass-bridge":
            self._handle_ingest_glass_bridge()
            return
        if parsed.path == "/v0/stripe/webhook":
            self._handle_stripe_webhook()
            return
        if parsed.path == "/v0/tokens/issue":
            self._handle_issue_token()
            return
        if parsed.path == "/v0/exchange/request":
            self._handle_exchange_request()
            return
        if parsed.path == "/v0/rewards/draft":
            self._handle_reward_draft()
            return
        if parsed.path.startswith("/v0/rewards/") and parsed.path.endswith(
            "/acknowledge"
        ):
            self._handle_acknowledge_reward()
            return
        if parsed.path.startswith("/v0/support-signals/") and parsed.path.endswith(
            "/resolve"
        ):
            self._handle_resolve_support_signal()
            return
        _json_response(
            self, status=HTTPStatus.NOT_FOUND, payload={"error": "not_found"}
        )

    def _handle_list_support_signals(self) -> None:
        """GET /v0/support-signals - list support signals with filters."""
        if not _require_operator_access(self):
            return

        parsed = urlparse(self.path)
        from urllib.parse import parse_qs

        qs = parse_qs(parsed.query)

        kind = qs.get("kind", [None])[0]
        resolved_str = qs.get("resolved", [None])[0]
        limit_str = qs.get("limit", ["50"])[0]

        resolved: bool | None = None
        if resolved_str is not None:
            resolved = resolved_str.lower() in ("true", "1", "yes")

        try:
            limit = int(limit_str)
        except ValueError:
            limit = 50

        with open_db(_get_db_path()) as conn:
            signals = list_support_signals(
                conn=conn, kind=kind, resolved=resolved, limit=limit
            )

        _json_response(
            self,
            status=HTTPStatus.OK,
            payload={"signals": signals, "count": len(signals)},
        )

    def _handle_outcome_summary(self) -> None:
        if not _require_operator_access(self):
            return

        parsed = urlparse(self.path)
        from urllib.parse import parse_qs

        qs = parse_qs(parsed.query)
        student_id = qs.get("student_id", [None])[0]

        with open_db(_get_db_path()) as conn:
            summary = get_outcome_summary(conn, student_id=student_id)

        _json_response(self, status=HTTPStatus.OK, payload=summary)

    def _handle_resolve_support_signal(self) -> None:
        """POST /v0/support-signals/<id>/resolve - mark signal as resolved."""
        if not _require_operator_access(self):
            return

        parsed = urlparse(self.path)
        parts = parsed.path.split("/")
        signal_id_str = parts[3] if len(parts) > 3 else None
        if not signal_id_str:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "missing_signal_id"},
            )
            return

        try:
            signal_id = int(signal_id_str)
        except ValueError:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "invalid_signal_id"},
            )
            return

        payload = _parse_body(self)
        if payload is None:
            return

        resolution_note = payload.get("resolution_note", "")

        with open_db(_get_db_path()) as conn:
            found = resolve_support_signal(
                conn=conn, signal_id=signal_id, resolution_note=str(resolution_note)
            )

        if not found:
            _json_response(
                self, status=HTTPStatus.NOT_FOUND, payload={"error": "signal_not_found"}
            )
            return

        _json_response(
            self, status=HTTPStatus.OK, payload={"ok": True, "signal_id": signal_id}
        )

    def _handle_acknowledge_reward(self) -> None:
        """POST /v0/rewards/<reward_id>/acknowledge - student confirmation after payment."""
        if not _require_operator_access(self):
            return

        parsed = urlparse(self.path)
        parts = parsed.path.split("/")
        reward_id = parts[3] if len(parts) > 3 else None
        if not reward_id:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "missing_reward_id"},
            )
            return

        payload = _parse_body(self)
        if payload is None:
            return

        student_id = payload.get("student_id")
        if not student_id:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "missing_required_fields", "need": ["student_id"]},
            )
            return

        notes = payload.get("notes")
        with open_db(_get_db_path()) as conn:
            result = acknowledge_reward(
                conn=conn,
                reward_id=str(reward_id),
                student_id=str(student_id),
                notes=str(notes) if notes else None,
            )

        if result.get("error"):
            status = (
                HTTPStatus.CONFLICT
                if result["error"]
                in ("ack_requires_payment_confirmed", "ack_student_mismatch")
                else HTTPStatus.BAD_REQUEST
            )
            _json_response(self, status=status, payload=result)
            return

        _json_response(self, status=HTTPStatus.OK, payload=result)

    def _handle_reward_draft(self) -> None:
        if not _require_operator_access(self):
            return
        payload = _parse_body(self)
        if payload is None:
            return

        reward_id = payload.get("reward_id")
        student_id = payload.get("student_id")
        if not reward_id or not student_id:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={
                    "error": "missing_required_fields",
                    "need": ["reward_id", "student_id"],
                },
            )
            return
        contract_id = str(payload.get("contract_id") or "psc-v0-default")
        amount_raw = payload.get("reward_token_amount", 1)
        try:
            amount = int(amount_raw)
        except (TypeError, ValueError):
            amount = 1
        with open_db(_get_db_path()) as conn:
            create_reward_draft(
                conn=conn,
                reward_id=str(reward_id),
                student_id=str(student_id),
                contract_id=contract_id,
                reward_token_amount=amount,
            )
        _json_response(
            self,
            status=HTTPStatus.OK,
            payload={"ok": True, "reward_id": str(reward_id)},
        )

    def _handle_ingest_glass_session(self) -> None:
        if not _require_operator_access(self):
            return

        payload = _parse_body(self)
        if payload is None:
            return

        session_id = payload.get("session_id") or payload.get("sessionId")
        student_id = payload.get("student_id") or payload.get("studentId")
        if not session_id or not student_id:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={
                    "error": "missing_required_fields",
                    "need": ["session_id", "student_id"],
                },
            )
            return

        with open_db(_get_db_path()) as conn:
            summary = ingest_glass_session(
                conn=conn,
                session_id=str(session_id),
                student_id=str(student_id),
                payload=payload,
            )
        _json_response(self, status=HTTPStatus.OK, payload=summary)

    def _handle_ingest_glass_bridge(self) -> None:
        if not _require_operator_access(self):
            return

        payload = _parse_body(self)
        if payload is None:
            return

        bridge = payload.get("bridge")
        if not isinstance(bridge, dict):
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "missing_or_invalid_bridge"},
            )
            return

        student_id = payload.get("student_id")
        if not student_id:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "missing_required_fields", "need": ["student_id"]},
            )
            return

        try:
            mapped = map_glass_bridge_to_ingest(
                bridge,
                student_id=str(student_id),
                reward_id=str(payload["reward_id"])
                if payload.get("reward_id")
                else None,
                contract_satisfied=bool(payload.get("contract_satisfied")),
                ready_for_payment=bool(payload.get("ready_for_payment")),
                student_ack=bool(payload.get("student_ack")),
                request_review=bool(payload.get("request_review")),
                failure=payload.get("failure")
                if isinstance(payload.get("failure"), dict)
                else None,
            )
        except ValueError as e:
            _json_response(
                self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)}
            )
            return

        with open_db(_get_db_path()) as conn:
            summary = ingest_glass_session(
                conn=conn,
                session_id=mapped["session_id"],
                student_id=mapped["student_id"],
                payload=mapped,
            )
        _json_response(self, status=HTTPStatus.OK, payload=summary)

    def _handle_stripe_webhook(self) -> None:
        stripe_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        if not stripe_secret:
            _json_response(
                self,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                payload={"error": "missing_STRIPE_WEBHOOK_SECRET"},
            )
            return

        max_bytes = _max_body_bytes()
        length = int(self.headers.get("Content-Length", "0"))
        if length > max_bytes:
            _json_response(
                self,
                status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                payload={"error": "body_too_large"},
            )
            return
        raw = self.rfile.read(min(length, max_bytes)) if length > 0 else b"{}"
        sig_header = self.headers.get("Stripe-Signature")
        tolerance_seconds = int(
            os.environ.get("XCHANGE_STRIPE_TOLERANCE_SECONDS", "300")
        )
        if not verify_stripe_signature(
            payload_body=raw,
            sig_header=sig_header,
            stripe_secret=stripe_secret,
            tolerance_seconds=tolerance_seconds,
        ):
            _json_response(
                self,
                status=HTTPStatus.UNAUTHORIZED,
                payload={"error": "invalid_stripe_signature"},
            )
            return

        try:
            event = json.loads(raw.decode("utf-8"))
        except Exception as e:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": f"invalid_json: {e}"},
            )
            return

        event_id = event.get("id")
        event_type = event.get("type")
        data_object = (event.get("data") or {}).get("object") or {}

        # Livemode guard: reject events whose livemode flag mismatches the server
        # expectation.  Only enforced when XCHANGE_LIVE_MODE is explicitly set.
        # Return 200 (not 4xx) so Stripe does not schedule retries.
        xchange_live_mode_env = os.environ.get("XCHANGE_LIVE_MODE")
        if xchange_live_mode_env is not None:
            expected_livemode = xchange_live_mode_env.lower() in ("true", "1", "yes")
            event_livemode = bool(event.get("livemode"))
            if event_livemode != expected_livemode:
                _json_response(
                    self,
                    status=HTTPStatus.OK,
                    payload={
                        "ignored": True,
                        "reason": "livemode_mismatch",
                        "event_livemode": event_livemode,
                        "expected_livemode": expected_livemode,
                    },
                )
                return

        if event_type != "payment_intent.succeeded":
            _json_response(
                self,
                status=HTTPStatus.OK,
                payload={"ignored": True, "reason": "unsupported_event_type"},
            )
            return

        if not isinstance(data_object, dict):
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "stripe_data_object_not_object"},
            )
            return

        metadata = data_object.get("metadata") or {}
        reward_id = metadata.get("reward_id")
        student_id = metadata.get("student_id")
        payment_intent_id = data_object.get("id")

        if not reward_id or not student_id or not event_id:
            with open_db(_get_db_path()) as conn:
                sid = insert_support_signal(
                    conn=conn,
                    kind="stripe_missing_metadata",
                    payload={
                        "event_id": event_id,
                        "event_type": event_type,
                        "has_reward_id": bool(reward_id),
                        "has_student_id": bool(student_id),
                    },
                )
            _json_response(
                self,
                status=HTTPStatus.OK,
                payload={
                    "accepted": True,
                    "support_signal_id": sid,
                    "reason": "missing_metadata",
                },
            )
            return

        with open_db(_get_db_path()) as conn:
            outcome = process_stripe_payment_intent_succeeded(
                conn=conn,
                stripe_event_id=str(event_id),
                stripe_payment_intent_id=str(payment_intent_id)
                if payment_intent_id
                else None,
                reward_id=str(reward_id),
                student_id=str(student_id),
                raw_event=event,
            )

            failure: FailureSnapshot | None = None
            if outcome.get("applied"):
                failure = latest_failure_for_student(conn, student_id=str(student_id))
                if failure:
                    suggestion = suggest_path_semantics(failure_command=failure.command)
                    create_nudge(
                        conn=conn,
                        student_id=str(student_id),
                        reward_id=str(reward_id),
                        failure_command=failure.command,
                        suggestion=suggestion,
                    )

        payload = {"stripe_event_id": str(event_id), **outcome}
        _json_response(self, status=HTTPStatus.OK, payload=payload)

    def _handle_issue_token(self) -> None:
        """POST /v0/tokens/issue — stamp an epistemic RewardToken on an existing reward.

        Required body fields: reward_id, insight_tier, base_bank_depth,
            inferential_richness, trend_position, issuance_trigger.
        rarity_score is always computed server-side — callers must not supply it.
        """
        if not _require_operator_access(self):
            return
        payload = _parse_body(self)
        if payload is None:
            return

        reward_id = payload.get("reward_id")
        insight_tier_raw = payload.get("insight_tier")
        issuance_trigger = payload.get("issuance_trigger")
        if not reward_id or not insight_tier_raw or not issuance_trigger:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={
                    "error": "missing_required_fields",
                    "need": ["reward_id", "insight_tier", "issuance_trigger"],
                },
            )
            return

        try:
            tier = InsightTier(str(insight_tier_raw))
        except ValueError:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={
                    "error": "invalid_insight_tier",
                    "valid": [t.value for t in InsightTier],
                },
            )
            return

        try:
            base_bank_depth = int(payload.get("base_bank_depth", 50))
            inferential_richness = float(payload.get("inferential_richness", 0.5))
            trend_position = float(payload.get("trend_position", 0.5))
        except (TypeError, ValueError) as e:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": f"invalid_numeric_field: {e}"},
            )
            return

        # Clamp numerics to valid ranges
        base_bank_depth = max(0, min(100, base_bank_depth))
        inferential_richness = max(0.0, min(1.0, inferential_richness))
        trend_position = max(0.0, min(1.0, trend_position))

        from datetime import datetime, timezone

        rarity_score = compute_rarity_score(
            insight_tier=tier,
            inferential_richness=inferential_richness,
            trend_position=trend_position,
        )
        token = RewardToken(
            insight_tier=tier,
            base_bank_depth=base_bank_depth,
            inferential_richness=inferential_richness,
            trend_position=trend_position,
            rarity_score=rarity_score,
            issuance_trigger=str(issuance_trigger),
            issued_at=datetime.now(timezone.utc).isoformat(),
        )

        with open_db(_get_db_path()) as conn:
            result = issue_reward_token(
                conn=conn, reward_id=str(reward_id), token=token
            )

        if result.get("error"):
            _json_response(self, status=HTTPStatus.NOT_FOUND, payload=result)
            return
        _json_response(self, status=HTTPStatus.OK, payload=result)

    def _handle_exchange_request(self) -> None:
        """POST /v0/exchange/request — evaluate and persist a token exchange request.

        Required body fields: request_id, student_id, reward_id, requested_scope.
        Constraint config is loaded from environment (not caller-supplied).
        """
        if not _require_operator_access(self):
            return
        payload = _parse_body(self)
        if payload is None:
            return

        request_id = payload.get("request_id")
        student_id = payload.get("student_id")
        reward_id = payload.get("reward_id")
        requested_scope = payload.get("requested_scope")
        if not request_id or not student_id or not reward_id:
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={
                    "error": "missing_required_fields",
                    "need": ["request_id", "student_id", "reward_id"],
                },
            )
            return
        if not isinstance(requested_scope, dict):
            _json_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                payload={"error": "requested_scope must be a JSON object"},
            )
            return

        from datetime import datetime, timezone

        exchange_request = ExchangeRequest(
            request_id=str(request_id),
            student_id=str(student_id),
            reward_id=str(reward_id),
            requested_scope=dict(requested_scope),
            submitted_at=datetime.now(timezone.utc).isoformat(),
        )
        config = _default_constraint_config()
        result = evaluate_exchange_request(exchange_request, config)

        config_snapshot = {
            "blocked_scope_keys": sorted(config.blocked_scope_keys),
            "irreversible_scope_keys": sorted(config.irreversible_scope_keys),
            "require_explicit_irreversible_approval": config.require_explicit_irreversible_approval,
            "max_token_amount": config.max_token_amount,
            "max_scope_items": config.max_scope_items,
        }

        with open_db(_get_db_path()) as conn:
            stored = store_exchange_request(
                conn=conn,
                request=exchange_request,
                result=result,
                constraint_config_snapshot=config_snapshot,
            )

        _json_response(self, status=HTTPStatus.OK, payload=stored)

    def _handle_list_exchange_requests(self) -> None:
        """GET /v0/exchange/requests — list exchange requests with optional filters.

        Query params: student_id, reward_id, approved (true/false), limit (int).
        """
        if not _require_operator_access(self):
            return

        parsed = urlparse(self.path)
        from urllib.parse import parse_qs

        qs = parse_qs(parsed.query)

        student_id = qs.get("student_id", [None])[0]
        reward_id = qs.get("reward_id", [None])[0]
        approved_str = qs.get("approved", [None])[0]
        limit_str = qs.get("limit", ["50"])[0]

        approved: bool | None = None
        if approved_str is not None:
            approved = approved_str.lower() in ("true", "1", "yes")

        try:
            limit = max(1, min(200, int(limit_str)))
        except ValueError:
            limit = 50

        with open_db(_get_db_path()) as conn:
            rows = list_exchange_requests(
                conn=conn,
                student_id=student_id,
                reward_id=reward_id,
                approved=approved,
                limit=limit,
            )

        _json_response(
            self,
            status=HTTPStatus.OK,
            payload={"exchange_requests": rows, "count": len(rows)},
        )


def _default_constraint_config() -> ConstraintConfig:
    """Build a ConstraintConfig from environment variables.

    Environment variables:
      XCHANGE_BLOCKED_SCOPE_KEYS         comma-separated, default empty
      XCHANGE_IRREVERSIBLE_SCOPE_KEYS    comma-separated, default 'delete,purge,ban,revoke'
      XCHANGE_REQUIRE_IRREVERSIBLE_APPROVAL  'true'/'false', default 'true'
      XCHANGE_MAX_TOKEN_AMOUNT           integer, default unlimited (None)
      XCHANGE_MAX_SCOPE_ITEMS            integer, default unlimited (None)
    """

    def _csv_frozenset(env_key: str, default: str) -> frozenset[str]:
        raw = os.environ.get(env_key, default)
        return frozenset(k.strip() for k in raw.split(",") if k.strip())

    blocked = _csv_frozenset("XCHANGE_BLOCKED_SCOPE_KEYS", "")
    irreversible = _csv_frozenset(
        "XCHANGE_IRREVERSIBLE_SCOPE_KEYS", "delete,purge,ban,revoke"
    )
    require_approval_str = os.environ.get(
        "XCHANGE_REQUIRE_IRREVERSIBLE_APPROVAL", "true"
    )
    require_approval = require_approval_str.lower() not in ("false", "0", "no")

    max_amount: int | None = None
    max_amount_raw = os.environ.get("XCHANGE_MAX_TOKEN_AMOUNT")
    if max_amount_raw:
        try:
            max_amount = int(max_amount_raw)
        except ValueError:
            pass

    max_items: int | None = None
    max_items_raw = os.environ.get("XCHANGE_MAX_SCOPE_ITEMS")
    if max_items_raw:
        try:
            max_items = int(max_items_raw)
        except ValueError:
            pass

    return ConstraintConfig(
        blocked_scope_keys=blocked,
        irreversible_scope_keys=irreversible,
        require_explicit_irreversible_approval=require_approval,
        max_token_amount=max_amount,
        max_scope_items=max_items,
    )


def run_server(*, host: str, port: int) -> None:
    httpd = HTTPServer((host, port), AppHandler)
    print(f"x-change v0 listening on http://{host}:{port}")
    httpd.serve_forever()
