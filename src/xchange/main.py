from __future__ import annotations

import hashlib
import json
import math
import os
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock
from typing import Any
from urllib.parse import urlparse

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
  latest_failure_for_student,
  list_support_signals,
  open_db,
  process_stripe_payment_intent_succeeded,
  resolve_support_signal,
)
from xchange.stripe_sig import verify_stripe_signature


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


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
  length = int(handler.headers.get("Content-Length", "0"))
  raw = handler.rfile.read(length) if length > 0 else b"{}"
  try:
    return json.loads(raw.decode("utf-8"))
  except Exception as e:
    raise ValueError(f"Invalid JSON: {e}") from e


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
    window_seconds = float(os.environ.get("XCHANGE_RATE_LIMIT_WINDOW_SECONDS", "60"))
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
    _json_response(handler, status=HTTPStatus.UNAUTHORIZED, payload={"error": "unauthorized"})
    return False
  return _enforce_operator_rate_limit(handler)


def _reset_rate_limit_for_tests() -> None:
  with _RATE_LIMIT_LOCK:
    _RATE_LIMIT_BUCKETS.clear()


def _get_db_path() -> str:
  return os.environ.get("XCHANGE_DB_PATH", "xchange.sqlite")


class AppHandler(BaseHTTPRequestHandler):
  server_version = "x-change/0"

  def do_GET(self) -> None:  # noqa: N802
    parsed = urlparse(self.path)
    if parsed.path.startswith("/v0/state/reward/"):
      if not _require_operator_access(self):
        return
      reward_id = parsed.path.split("/v0/state/reward/")[1]
      reward_id = reward_id.split("?")[0].strip() or reward_id
      with open_db(_get_db_path()) as conn:
        state = get_reward_state(conn, reward_id=reward_id)
      if not state:
        _json_response(self, status=HTTPStatus.NOT_FOUND, payload={"error": "reward_not_found"})
        return
      _json_response(self, status=HTTPStatus.OK, payload=state)
      return

    if parsed.path == "/v0/support-signals":
      self._handle_list_support_signals()
      return

    if parsed.path == "/v0/outcomes/summary":
      self._handle_outcome_summary()
      return

    _json_response(self, status=HTTPStatus.NOT_FOUND, payload={"error": "not_found"})

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
    if parsed.path == "/v0/rewards/draft":
      self._handle_reward_draft()
      return
    if parsed.path.startswith("/v0/rewards/") and parsed.path.endswith("/acknowledge"):
      self._handle_acknowledge_reward()
      return
    if parsed.path.startswith("/v0/support-signals/") and parsed.path.endswith("/resolve"):
      self._handle_resolve_support_signal()
      return
    _json_response(self, status=HTTPStatus.NOT_FOUND, payload={"error": "not_found"})

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
      signals = list_support_signals(conn=conn, kind=kind, resolved=resolved, limit=limit)
    
    _json_response(self, status=HTTPStatus.OK, payload={"signals": signals, "count": len(signals)})

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
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": "missing_signal_id"})
      return
    
    try:
      signal_id = int(signal_id_str)
    except ValueError:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": "invalid_signal_id"})
      return
    
    try:
      payload = _read_json_body(self)
    except ValueError as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)})
      return
    
    resolution_note = payload.get("resolution_note", "")
    
    with open_db(_get_db_path()) as conn:
      found = resolve_support_signal(conn=conn, signal_id=signal_id, resolution_note=str(resolution_note))
    
    if not found:
      _json_response(self, status=HTTPStatus.NOT_FOUND, payload={"error": "signal_not_found"})
      return
    
    _json_response(self, status=HTTPStatus.OK, payload={"ok": True, "signal_id": signal_id})

  def _handle_acknowledge_reward(self) -> None:
    """POST /v0/rewards/<reward_id>/acknowledge - student confirmation after payment."""
    if not _require_operator_access(self):
      return
    
    parsed = urlparse(self.path)
    parts = parsed.path.split("/")
    reward_id = parts[3] if len(parts) > 3 else None
    if not reward_id:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": "missing_reward_id"})
      return
    
    try:
      payload = _read_json_body(self)
    except ValueError as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)})
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
      status = HTTPStatus.CONFLICT if result["error"] in ("ack_requires_payment_confirmed", "ack_student_mismatch") else HTTPStatus.BAD_REQUEST
      _json_response(self, status=status, payload=result)
      return
    
    _json_response(self, status=HTTPStatus.OK, payload=result)

  def _handle_reward_draft(self) -> None:
    if not _require_operator_access(self):
      return
    try:
      payload = _read_json_body(self)
    except ValueError as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)})
      return

    reward_id = payload.get("reward_id")
    student_id = payload.get("student_id")
    if not reward_id or not student_id:
      _json_response(
        self,
        status=HTTPStatus.BAD_REQUEST,
        payload={"error": "missing_required_fields", "need": ["reward_id", "student_id"]},
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
    _json_response(self, status=HTTPStatus.OK, payload={"ok": True, "reward_id": str(reward_id)})

  def _handle_ingest_glass_session(self) -> None:
    if not _require_operator_access(self):
      return

    try:
      payload = _read_json_body(self)
    except ValueError as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)})
      return

    session_id = payload.get("session_id") or payload.get("sessionId")
    student_id = payload.get("student_id") or payload.get("studentId")
    if not session_id or not student_id:
      _json_response(
        self,
        status=HTTPStatus.BAD_REQUEST,
        payload={"error": "missing_required_fields", "need": ["session_id", "student_id"]},
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

    try:
      payload = _read_json_body(self)
    except ValueError as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)})
      return

    bridge = payload.get("bridge")
    if not isinstance(bridge, dict):
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": "missing_or_invalid_bridge"})
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
        reward_id=str(payload["reward_id"]) if payload.get("reward_id") else None,
        contract_satisfied=bool(payload.get("contract_satisfied")),
        ready_for_payment=bool(payload.get("ready_for_payment")),
        student_ack=bool(payload.get("student_ack")),
        request_review=bool(payload.get("request_review")),
        failure=payload.get("failure") if isinstance(payload.get("failure"), dict) else None,
      )
    except ValueError as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": str(e)})
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
      _json_response(self, status=HTTPStatus.INTERNAL_SERVER_ERROR, payload={"error": "missing_STRIPE_WEBHOOK_SECRET"})
      return

    length = int(self.headers.get("Content-Length", "0"))
    raw = self.rfile.read(length) if length > 0 else b"{}"
    sig_header = self.headers.get("Stripe-Signature")
    tolerance_seconds = int(os.environ.get("XCHANGE_STRIPE_TOLERANCE_SECONDS", "300"))
    if not verify_stripe_signature(
      payload_body=raw,
      sig_header=sig_header,
      stripe_secret=stripe_secret,
      tolerance_seconds=tolerance_seconds,
    ):
      _json_response(self, status=HTTPStatus.UNAUTHORIZED, payload={"error": "invalid_stripe_signature"})
      return

    try:
      event = json.loads(raw.decode("utf-8"))
    except Exception as e:
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": f"invalid_json: {e}"})
      return

    event_id = event.get("id")
    event_type = event.get("type")
    data_object = (event.get("data") or {}).get("object") or {}

    if event_type != "payment_intent.succeeded":
      _json_response(self, status=HTTPStatus.OK, payload={"ignored": True, "reason": "unsupported_event_type"})
      return

    if not isinstance(data_object, dict):
      _json_response(self, status=HTTPStatus.BAD_REQUEST, payload={"error": "stripe_data_object_not_object"})
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
        stripe_payment_intent_id=str(payment_intent_id) if payment_intent_id else None,
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


def run_server(*, host: str, port: int) -> None:
  httpd = HTTPServer((host, port), AppHandler)
  print(f"x-change v0 listening on http://{host}:{port}")
  httpd.serve_forever()
