from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Final

from xchange.domain import (
    DEFAULT_CONTRACT_ID,
    POLICY_VERSION,
    EvidenceType,
    ExchangeRequest,
    ExchangeResult,
    InsightTier,
    OutcomeState,
    PaymentConfirmationStatus,
    RewardState,
    RewardToken,
    TokenScope,
    ToolProvenance,
    ToolScope,
    TransitionResult,
    ingest_bool,
    infer_token_scope,
    next_state_after_glass_evidence,
    next_state_after_stripe_payment,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RewardTokenAmount:
    """Typed wrapper for reward token quantity (units).

    Preserves semantic type information: a RewardTokenAmount is not just
    any integer, but specifically a count of reward token units.
    """
    units: int

    def __init__(self, units: int) -> None:
        object.__setattr__(self, "units", max(0, int(units)))

    def __str__(self) -> str:
        return str(self.units)

    def __repr__(self) -> str:
        return f"RewardTokenAmount(units={self.units})"


LEGACY_SCHEMA_SQL: Final[str] = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS failures (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  command TEXT,
  exit_code INTEGER,
  stdout_text TEXT,
  stderr_text TEXT,
  failure_at TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rewards (
  reward_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  delivered INTEGER NOT NULL DEFAULT 0,
  delivered_at TEXT,
  stripe_event_id TEXT,
  stripe_payment_intent_id TEXT,
  last_payload_json TEXT
);

CREATE TABLE IF NOT EXISTS nudges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT NOT NULL,
  reward_id TEXT,
  created_at TEXT NOT NULL,
  failure_command TEXT,
  suggestion TEXT NOT NULL
);
"""

CORE_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS service_contracts (
  contract_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  promise_json TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reward_ledger (
  reward_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  contract_id TEXT NOT NULL,
  state TEXT NOT NULL,
  reward_token_amount INTEGER NOT NULL DEFAULT 0,
  outcome_state TEXT NOT NULL DEFAULT 'unknown',
  student_acknowledged_at TEXT,
  review_requested_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  notes_json TEXT,
  FOREIGN KEY(contract_id) REFERENCES service_contracts(contract_id)
);

CREATE TABLE IF NOT EXISTS evidence_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reward_id TEXT,
  student_id TEXT NOT NULL,
  session_id TEXT,
  evidence_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  provenance TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_confirmations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stripe_event_id TEXT NOT NULL UNIQUE,
  stripe_payment_intent_id TEXT,
  reward_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  raw_event_json TEXT NOT NULL,
  status TEXT NOT NULL,
  applied_at TEXT,
  provenance TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS support_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS exchange_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id TEXT NOT NULL UNIQUE,
  reward_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  requested_scope_json TEXT NOT NULL,
  constraint_config_json TEXT NOT NULL,
  constraint_result_json TEXT NOT NULL,
  approved INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stripe_event_id TEXT NOT NULL UNIQUE,
  event_type TEXT NOT NULL,
  livemode INTEGER NOT NULL DEFAULT 0,
  received_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_reward ON evidence_ledger(reward_id);
CREATE INDEX IF NOT EXISTS idx_evidence_student ON evidence_ledger(student_id);
CREATE INDEX IF NOT EXISTS idx_payment_reward ON payment_confirmations(reward_id);
CREATE INDEX IF NOT EXISTS idx_exchange_reward ON exchange_requests(reward_id);
CREATE INDEX IF NOT EXISTS idx_exchange_student ON exchange_requests(student_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type);
"""

# Operator/orchestrator memos from parallel agents (INSERT OR IGNORE — idempotent).
_INBOX_ORCHESTRATOR_MEMOS: Final[
    tuple[tuple[str, str, str, str, str, str], ...]
] = (
    (
        "memo-grid-slices-2-5",
        "GRID-main agent",
        "626450",
        "/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main",
        "GRID Slices 2–5: route normalization, event bus, DDD fix, docs",
        """Slice 2 — Route normalization
- corruption, admission, drt, safety routers moved from app.include_router() → api_router.include_router(), landing them under /api/v1/*
- health_router, /ping, /, /security/status remain root-level (operational)
- Added two new test cases to tests/integration/test_mothership_route_map.py locking versioned paths and asserting root-level product paths are gone

Slice 3 — Event bus cleanup
- Fixed double-delivery bug in src/grid/agentic/event_bus.py: removed event_queue.put() from publish(), leaving _trigger_handlers() as the single delivery path
- Added await event_bus.start() and app.state.infrastructure_event_bus in lifespan startup; await stop() on shutdown

Slice 4 — DDD inversion fix
- main.py had wrong dispose wiring (set_dispose_engine vs wire_dispose_engine); injection was silently no-op — corrected to wire_dispose_engine
- PrunerOrchestrator gains dispose-engine hooks; removed application-layer import from infrastructure dispose path

Slice 5 — Docs
- docs/ARCHITECTURE.md bumped to v2.8.0 (May 2026): router map, ownership appendix (event bus matrix, safety/security, DDD boundaries)
""",
    ),
    (
        "memo-xchange-scope",
        "x-change agent",
        "parallel-session",
        "/home/irfankabir/x-change",
        "x-change: Token/Tool scope layer + tests",
        """Completed: Token scope + Tool scope definition and implementation

Docs (docs/):
- token-scope.md — RewardToken semantics; tier/rarity/exchange; not currency/signal/license
- tool-scope.md — tools (Glass, GRID, Calculator), evidence, no-auto-inference, provenance
- scope-integration.md — tool → evidence → reward → token; payload traces; organic scope

Code:
- domain.py — ToolProvenance enum, TokenScope, ToolScope, infer_token_scope()
- storage.py — resolve_token_scope(), resolve_tool_scope()
- main.py — GET /v0/scope/token/<reward_id>, GET /v0/scope/tool?provenance=

Tests: tests/test_scope.py (scope resolution + API parsing); full suite green at time of memo.

See live reward scope via authorized GET /v0/scope/token/reward-circuit-close-001.
""",
    ),
)


@dataclass(frozen=True)
class FailureSnapshot:
    command: str | None
    exit_code: int | None
    stdout_text: str | None
    stderr_text: str | None
    failure_at: str
    payload: dict[str, Any]


def _ensure_default_contract(conn: sqlite3.Connection) -> None:
    now = _utc_now_iso()
    promise = {
        "summary": "Default x-change v0 principled service promise (see docs/policy-core-v0.md).",
        "policy": POLICY_VERSION,
    }
    conn.execute(
        """
    INSERT OR IGNORE INTO service_contracts (contract_id, title, promise_json, policy_version, created_at)
    VALUES (?, ?, ?, ?, ?)
    """,
        (
            DEFAULT_CONTRACT_ID,
            "x-change v0 default PSC",
            json.dumps(promise, ensure_ascii=False),
            POLICY_VERSION,
            now,
        ),
    )


def _migrate_legacy_rewards(conn: sqlite3.Connection) -> None:
    """Migrate legacy rewards table to reward_ledger, tracked in schema_migrations.

    Uses schema_migrations table as authoritative log, not row count heuristic.
    """
    migration_version = "v000_legacy_rewards_ingest"
    cur = conn.execute(
        "SELECT version FROM schema_migrations WHERE version=?", (migration_version,)
    )
    if cur.fetchone():
        return  # already migrated

    legacy = conn.execute(
        "SELECT reward_id, student_id, delivered FROM rewards"
    ).fetchall()
    now = _utc_now_iso()
    for lr in legacy:
        rid = str(lr["reward_id"])
        sid = str(lr["student_id"])
        delivered = int(lr["delivered"])
        state = RewardState.PAYMENT_CONFIRMED if delivered else RewardState.DRAFTED
        outcome = (
            OutcomeState.DELIVERED_PENDING_ACK if delivered else OutcomeState.UNKNOWN
        )
        conn.execute(
            """
      INSERT OR IGNORE INTO reward_ledger (
        reward_id, student_id, contract_id, state, reward_token_amount, outcome_state,
        student_acknowledged_at, review_requested_at, created_at, updated_at, notes_json
      ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
      """,
            (
                rid,
                sid,
                DEFAULT_CONTRACT_ID,
                state.value,
                1,
                outcome.value,
                now,
                now,
                json.dumps({"migrated_from": "rewards"}, ensure_ascii=False),
            ),
        )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        (migration_version, now),
    )
    conn.commit()


def _run_migration(conn: sqlite3.Connection, version: str, sql: str) -> bool:
    """Apply a one-time schema migration if it hasn't been recorded yet.

    Uses the schema_migrations table as the authoritative migration log.
    Returns True if the migration was applied this call, False if already recorded.
    Silently absorbs OperationalError (e.g. duplicate column) so an upgraded DB
    that already has the column still gets its version recorded.
    """
    cur = conn.execute(
        "SELECT version FROM schema_migrations WHERE version=?", (version,)
    )
    if cur.fetchone():
        return False  # already applied
    try:
        conn.executescript(sql)
    except sqlite3.OperationalError:
        # Migration SQL already partially applied (e.g. column exists).
        # Record as applied so we don't retry on every startup.
        pass
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        (version, _utc_now_iso()),
    )
    conn.commit()
    return True


def _seed_orchestrator_inbox_memos(conn: sqlite3.Connection) -> None:
    """Load canonical parallel-agent memos once per empty id (INSERT OR IGNORE)."""
    now = _utc_now_iso()
    for (
        memo_id,
        source,
        pid,
        cwd,
        title,
        content,
    ) in _INBOX_ORCHESTRATOR_MEMOS:
        conn.execute(
            """
            INSERT OR IGNORE INTO inbox_entries
            (id, source, pid, cwd, title, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'unprocessed', ?)
            """,
            (memo_id, source, pid, cwd, title, content, now),
        )
    conn.commit()


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(LEGACY_SCHEMA_SQL)
    conn.executescript(CORE_SCHEMA_SQL)
    _ensure_default_contract(conn)
    _migrate_legacy_rewards(conn)
    conn.commit()
    # Additive column migrations — safe to replay (recorded in schema_migrations).
    _run_migration(
        conn,
        "v001_reward_token_json",
        "ALTER TABLE reward_ledger ADD COLUMN reward_token_json TEXT;",
    )
    _run_migration(
        conn,
        "v002_inbox_entries",
        """
CREATE TABLE IF NOT EXISTS inbox_entries (
  id TEXT PRIMARY KEY,
  source TEXT,
  pid TEXT,
  cwd TEXT,
  title TEXT,
  content TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unprocessed',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inbox_entries_created_at ON inbox_entries(created_at);
""",
    )
    _run_migration(
        conn,
        "v003_session_memory",
        """
CREATE TABLE IF NOT EXISTS session_memory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  memory_key TEXT NOT NULL,
  memory_value TEXT NOT NULL,
  source_path TEXT NOT NULL,
  scope TEXT NOT NULL DEFAULT 'x-change',
  session_id TEXT,
  is_stale INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  stale_checked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_session_memory_key ON session_memory(memory_key);
CREATE INDEX IF NOT EXISTS idx_session_memory_scope ON session_memory(scope);
CREATE INDEX IF NOT EXISTS idx_session_memory_stale ON session_memory(is_stale);
""",
    )
    _seed_orchestrator_inbox_memos(conn)


@contextmanager
def open_db(db_path: str):
    conn = sqlite3.connect(db_path)
    # Enforce strict permissions (0600: owner read/write only) on the database file
    # to prevent local information disclosure.
    try:
        os.chmod(db_path, 0o600)
    except OSError:
        pass  # E.g., if we don't own the file or it's an in-memory DB

    conn.row_factory = sqlite3.Row
    try:
        init_db(conn)
        yield conn
    finally:
        conn.close()


def insert_support_signal(
    *, conn: sqlite3.Connection, kind: str, payload: dict[str, Any]
) -> int:
    cur = conn.execute(
        """
    INSERT INTO support_signals (kind, payload_json, created_at)
    VALUES (?, ?, ?)
    """,
        (kind, json.dumps(payload, ensure_ascii=False), _utc_now_iso()),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def list_support_signals(
    *,
    conn: sqlite3.Connection,
    kind: str | None = None,
    resolved: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List support signals with optional filters."""
    where_clauses: list[str] = []
    params: list[Any] = []

    if kind is not None:
        where_clauses.append("kind=?")
        params.append(kind)

    if resolved is not None:
        if resolved:
            where_clauses.append("resolved_at IS NOT NULL")
        else:
            where_clauses.append("resolved_at IS NULL")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    params.append(limit)
    params.append(offset)

    query = f"""
    SELECT id, kind, payload_json, created_at, resolved_at
    FROM support_signals
    WHERE {where_sql}
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
  """

    rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": row["id"],
            "kind": row["kind"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
            "resolved_at": row["resolved_at"],
        }
        for row in rows
    ]


def resolve_support_signal(
    *,
    conn: sqlite3.Connection,
    signal_id: int,
    resolution_note: str,
) -> bool:
    """Mark a support signal as resolved. Returns True if signal was found."""
    cur = conn.execute(
        "SELECT id, payload_json FROM support_signals WHERE id=?",
        (signal_id,),
    )
    row = cur.fetchone()
    if not row:
        return False

    payload = json.loads(row["payload_json"])
    payload["resolution"] = {"resolution_note": resolution_note}

    conn.execute(
        """
    UPDATE support_signals
    SET resolved_at=?, payload_json=?
    WHERE id=?
    """,
        (_utc_now_iso(), json.dumps(payload, ensure_ascii=False), signal_id),
    )
    conn.commit()
    return True


def create_reward_draft(
    *,
    conn: sqlite3.Connection,
    reward_id: str,
    student_id: str,
    contract_id: str = DEFAULT_CONTRACT_ID,
    reward_token_amount: int = 1,
) -> None:
    now = _utc_now_iso()
    conn.execute(
        """
    INSERT INTO reward_ledger (
      reward_id, student_id, contract_id, state, reward_token_amount, outcome_state,
      student_acknowledged_at, review_requested_at, created_at, updated_at, notes_json
    ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL)
    ON CONFLICT(reward_id) DO NOTHING
    """,
        (
            reward_id,
            student_id,
            contract_id,
            RewardState.DRAFTED.value,
            reward_token_amount,
            OutcomeState.UNKNOWN.value,
            now,
            now,
        ),
    )
    conn.commit()


def append_evidence(
    *,
    conn: sqlite3.Connection,
    student_id: str,
    session_id: str | None,
    reward_id: str | None,
    evidence_type: EvidenceType,
    payload: dict[str, Any],
    provenance: str,
) -> int:
    cur = conn.execute(
        """
    INSERT INTO evidence_ledger (
      reward_id, student_id, session_id, evidence_type, payload_json, provenance, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            reward_id,
            student_id,
            session_id,
            evidence_type.value,
            json.dumps(payload, ensure_ascii=False),
            provenance,
            _utc_now_iso(),
        ),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def _load_reward_row(conn: sqlite3.Connection, reward_id: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM reward_ledger WHERE reward_id=?", (reward_id,))
    return cur.fetchone()


def _apply_transition(
    conn: sqlite3.Connection,
    *,
    reward_id: str,
    result: TransitionResult,
    extra_notes: list[str] | None = None,
) -> None:
    row = _load_reward_row(conn, reward_id)
    if not row:
        return
    prior = json.loads(row["notes_json"]) if row["notes_json"] else {}
    log = list(prior.get("transition_log", []))
    entry_notes: list[str] = list(result.notes)
    if extra_notes:
        entry_notes.extend(extra_notes)
    entry = {"at": _utc_now_iso(), "notes": entry_notes}
    log.append(entry)
    prior["transition_log"] = log
    now = _utc_now_iso()
    ack_at = row["student_acknowledged_at"]
    if result.new_state is RewardState.STUDENT_ACKNOWLEDGED:
        ack_at = now
    review_at = row["review_requested_at"]
    if result.new_state is RewardState.REVIEW_REQUESTED:
        review_at = now
    conn.execute(
        """
    UPDATE reward_ledger SET
      state=?,
      outcome_state=?,
      student_acknowledged_at=?,
      review_requested_at=?,
      updated_at=?,
      notes_json=?
    WHERE reward_id=?
    """,
        (
            result.new_state.value,
            result.new_outcome.value,
            ack_at,
            review_at,
            now,
            json.dumps(prior, ensure_ascii=False),
            reward_id,
        ),
    )


def apply_evidence_to_reward(
    *,
    conn: sqlite3.Connection,
    reward_id: str,
    evidence_type: EvidenceType,
    ingest_payload: dict[str, Any],
) -> TransitionResult | None:
    row = _load_reward_row(conn, reward_id)
    if not row:
        return None
    current = RewardState(str(row["state"]))
    outcome = OutcomeState(str(row["outcome_state"]))
    proposal = next_state_after_glass_evidence(
        current=current,
        outcome=outcome,
        evidence_type=evidence_type,
        ingest_payload=ingest_payload,
    )
    if proposal:
        _apply_transition(conn, reward_id=reward_id, result=proposal)
    return proposal


def upsert_session(
    *,
    conn: sqlite3.Connection,
    session_id: str,
    student_id: str,
    payload: dict[str, Any],
) -> None:
    now = _utc_now_iso()
    conn.execute(
        """
    INSERT INTO sessions (session_id, student_id, created_at, payload_json)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
      student_id=excluded.student_id,
      payload_json=excluded.payload_json
    """,
        (session_id, student_id, now, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()


def record_failure(
    *,
    conn: sqlite3.Connection,
    session_id: str,
    student_id: str,
    failure: dict[str, Any],
) -> FailureSnapshot:
    now = failure.get("failure_at") or _utc_now_iso()
    command = failure.get("command")
    exit_code = failure.get("exit_code")
    stdout_text = failure.get("stdout")
    stderr_text = failure.get("stderr")

    conn.execute(
        """
    INSERT INTO failures (session_id, student_id, command, exit_code, stdout_text, stderr_text, failure_at, payload_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            session_id,
            student_id,
            command,
            exit_code,
            stdout_text,
            stderr_text,
            now,
            json.dumps(failure, ensure_ascii=False),
        ),
    )
    conn.commit()
    return FailureSnapshot(
        command=command,
        exit_code=exit_code,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        failure_at=now,
        payload=failure,
    )


def latest_failure_for_student(
    conn: sqlite3.Connection, *, student_id: str
) -> FailureSnapshot | None:
    cur = conn.execute(
        """
    SELECT command, exit_code, stdout_text, stderr_text, failure_at, payload_json
    FROM failures
    WHERE student_id=?
    ORDER BY failure_at DESC
    LIMIT 1
    """,
        (student_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    payload = json.loads(row["payload_json"])
    return FailureSnapshot(
        command=row["command"],
        exit_code=row["exit_code"],
        stdout_text=row["stdout_text"],
        stderr_text=row["stderr_text"],
        failure_at=row["failure_at"],
        payload=payload,
    )


def ingest_glass_session(
    *,
    conn: sqlite3.Connection,
    session_id: str,
    student_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Persist session + evidence and optionally transition reward state."""

    upsert_session(
        conn=conn, session_id=session_id, student_id=student_id, payload=payload
    )

    reward_id = payload.get("reward_id")
    rid = str(reward_id) if reward_id else None

    append_evidence(
        conn=conn,
        student_id=student_id,
        session_id=session_id,
        reward_id=rid,
        evidence_type=EvidenceType.GLASS_SESSION_EVENT,
        payload=payload,
        provenance="glass_ingest",
    )

    transition: TransitionResult | None = None
    if rid:
        transition = apply_evidence_to_reward(
            conn=conn,
            reward_id=rid,
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
            ingest_payload=payload,
        )

    failure = payload.get("failure")
    if isinstance(failure, dict):
        record_failure(
            conn=conn, session_id=session_id, student_id=student_id, failure=failure
        )
        append_evidence(
            conn=conn,
            student_id=student_id,
            session_id=session_id,
            reward_id=rid,
            evidence_type=EvidenceType.FAILURE_SNAPSHOT,
            payload=failure,
            provenance="glass_ingest",
        )
        if rid:
            t2 = apply_evidence_to_reward(
                conn=conn,
                reward_id=rid,
                evidence_type=EvidenceType.FAILURE_SNAPSHOT,
                ingest_payload=payload,
            )
            transition = t2 or transition

    if rid and ingest_bool(payload, "student_ack"):
        # DEPRECATED: Use POST /v0/rewards/<reward_id>/acknowledge instead.
        # This path kept for backward compatibility.
        t3 = apply_evidence_to_reward(
            conn=conn,
            reward_id=rid,
            evidence_type=EvidenceType.STUDENT_CONFIRMATION,
            ingest_payload=payload,
        )
        transition = t3 or transition

    conn.commit()
    out: dict[str, Any] = {"ok": True, "evidence_recorded": True}
    if transition:
        out["transition"] = {
            "new_state": transition.new_state.value,
            "new_outcome": transition.new_outcome.value,
            "notes": list(transition.notes),
        }
    return out


def upsert_reward_delivery(
    *,
    conn: sqlite3.Connection,
    reward_id: str,
    student_id: str,
    stripe_event_id: str,
    stripe_payment_intent_id: str | None,
    payload: dict[str, Any],
) -> None:
    """Legacy mirror: keep rewards table updated for transitional readers."""

    now = _utc_now_iso()
    conn.execute(
        """
    INSERT INTO rewards (reward_id, student_id, delivered, delivered_at, stripe_event_id, stripe_payment_intent_id, last_payload_json)
    VALUES (?, ?, 1, ?, ?, ?, ?)
    ON CONFLICT(reward_id) DO UPDATE SET
      student_id=excluded.student_id,
      delivered=1,
      delivered_at=excluded.delivered_at,
      stripe_event_id=excluded.stripe_event_id,
      stripe_payment_intent_id=excluded.stripe_payment_intent_id,
      last_payload_json=excluded.last_payload_json
    """,
        (
            reward_id,
            student_id,
            now,
            stripe_event_id,
            stripe_payment_intent_id,
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    conn.commit()


def record_webhook_event(
    conn: sqlite3.Connection,
    *,
    stripe_event_id: str,
    event_type: str,
    livemode: bool,
) -> bool:
    """Record an incoming Stripe webhook event for idempotency dedup.

    Uses INSERT OR IGNORE so the call is safe to replay.

    Returns:
        True  — event was new and has been recorded.
        False — event_id already seen; caller should return 200 immediately.
    """
    now = _utc_now_iso()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO webhook_events
          (stripe_event_id, event_type, livemode, received_at)
        VALUES (?, ?, ?, ?)
        """,
        (stripe_event_id, event_type, 1 if livemode else 0, now),
    )
    conn.commit()
    return cur.rowcount == 1


def process_stripe_payment_intent_succeeded(
    *,
    conn: sqlite3.Connection,
    stripe_event_id: str,
    stripe_payment_intent_id: str | None,
    reward_id: str,
    student_id: str,
    raw_event: dict[str, Any],
) -> dict[str, Any]:
    """Idempotent payment confirmation row + reward transition. Returns summary for HTTP layer."""

    now = _utc_now_iso()
    try:
        conn.execute(
            """
      INSERT INTO payment_confirmations (
        stripe_event_id, stripe_payment_intent_id, reward_id, student_id,
        raw_event_json, status, applied_at, provenance, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
      """,
            (
                stripe_event_id,
                stripe_payment_intent_id,
                reward_id,
                student_id,
                json.dumps(raw_event, ensure_ascii=False),
                PaymentConfirmationStatus.RECEIVED.value,
                "stripe_webhook",
                now,
            ),
        )
    except sqlite3.IntegrityError:
        conn.rollback()
        return {"duplicate": True, "stripe_event_id": stripe_event_id}

    row = _load_reward_row(conn, reward_id)
    if not row:
        insert_support_signal(
            conn=conn,
            kind="stripe_reward_missing",
            payload={
                "reward_id": reward_id,
                "student_id": student_id,
                "stripe_event_id": stripe_event_id,
            },
        )
        conn.execute(
            """
      UPDATE payment_confirmations SET status=?, applied_at=? WHERE stripe_event_id=?
      """,
            (
                PaymentConfirmationStatus.NOT_APPLIED_MISMATCH.value,
                now,
                stripe_event_id,
            ),
        )
        conn.commit()
        return {
            "applied": False,
            "reason": "reward_missing",
            "stripe_event_id": stripe_event_id,
        }

    ledger_student = str(row["student_id"])
    if ledger_student != student_id:
        insert_support_signal(
            conn=conn,
            kind="stripe_student_mismatch",
            payload={
                "reward_id": reward_id,
                "metadata_student_id": student_id,
                "ledger_student_id": ledger_student,
                "stripe_event_id": stripe_event_id,
            },
        )
        conn.execute(
            """
      UPDATE payment_confirmations SET status=?, applied_at=? WHERE stripe_event_id=?
      """,
            (
                PaymentConfirmationStatus.NOT_APPLIED_MISMATCH.value,
                now,
                stripe_event_id,
            ),
        )
        conn.commit()
        return {
            "applied": False,
            "reason": "student_mismatch",
            "stripe_event_id": stripe_event_id,
        }

    current = RewardState(str(row["state"]))
    outcome = OutcomeState(str(row["outcome_state"]))
    proposal = next_state_after_stripe_payment(
        current=current,
        outcome=outcome,
        reward_student_id=ledger_student,
        payment_student_id=student_id,
    )
    if proposal is None:
        insert_support_signal(
            conn=conn,
            kind="stripe_student_mismatch",
            payload={"reward_id": reward_id, "stripe_event_id": stripe_event_id},
        )
        conn.execute(
            """
      UPDATE payment_confirmations SET status=?, applied_at=? WHERE stripe_event_id=?
      """,
            (
                PaymentConfirmationStatus.NOT_APPLIED_MISMATCH.value,
                now,
                stripe_event_id,
            ),
        )
        conn.commit()
        return {
            "applied": False,
            "reason": "student_mismatch",
            "stripe_event_id": stripe_event_id,
        }

    became_confirmed = (
        proposal.new_state is RewardState.PAYMENT_CONFIRMED
        and current
        in (
            RewardState.EARNED,
            RewardState.PAYMENT_PENDING,
        )
    )

    if proposal.new_state is RewardState.PAYMENT_CONFIRMED:
        _apply_transition(conn, reward_id=reward_id, result=proposal)
        pay_status = (
            PaymentConfirmationStatus.APPLIED.value
            if became_confirmed
            else PaymentConfirmationStatus.DUPLICATE_IGNORED.value
        )
        conn.execute(
            """
      UPDATE payment_confirmations SET status=?, applied_at=? WHERE stripe_event_id=?
      """,
            (pay_status, now, stripe_event_id),
        )
        if became_confirmed:
            upsert_reward_delivery(
                conn=conn,
                reward_id=reward_id,
                student_id=ledger_student,
                stripe_event_id=stripe_event_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                payload=raw_event,
            )
    else:
        conn.execute(
            """
      UPDATE payment_confirmations SET status=?, applied_at=? WHERE stripe_event_id=?
      """,
            (
                PaymentConfirmationStatus.NOT_APPLIED_MISMATCH.value,
                now,
                stripe_event_id,
            ),
        )
    conn.commit()
    return {
        "applied": became_confirmed,
        "stripe_event_id": stripe_event_id,
        "new_state": proposal.new_state.value,
        "notes": list(proposal.notes),
    }


def get_reward_state(
    conn: sqlite3.Connection, *, reward_id: str
) -> dict[str, Any] | None:
    row = _load_reward_row(conn, reward_id)
    if not row:
        return None

    evidence = conn.execute(
        """
    SELECT id, evidence_type, provenance, created_at, payload_json
    FROM evidence_ledger
    WHERE reward_id=?
    ORDER BY id ASC
    """,
        (reward_id,),
    ).fetchall()

    evidence_out: list[dict[str, Any]] = []
    for er in evidence:
        evidence_out.append(
            {
                "id": er["id"],
                "evidence_type": er["evidence_type"],
                "provenance": er["provenance"],
                "created_at": er["created_at"],
                "payload": json.loads(er["payload_json"])
                if er["payload_json"]
                else None,
            }
        )

    payments = conn.execute(
        """
    SELECT stripe_event_id, status, created_at, applied_at
    FROM payment_confirmations
    WHERE reward_id=?
    ORDER BY id ASC
    """,
        (reward_id,),
    ).fetchall()

    legacy = conn.execute(
        "SELECT * FROM rewards WHERE reward_id=?", (reward_id,)
    ).fetchone()

    return {
        "reward_id": row["reward_id"],
        "student_id": row["student_id"],
        "contract_id": row["contract_id"],
        "state": row["state"],
        "reward_token_amount": RewardTokenAmount(int(row["reward_token_amount"])),
        "reward_token": json.loads(row["reward_token_json"])
        if row["reward_token_json"]
        else None,
        "outcome_state": row["outcome_state"],
        "student_acknowledged_at": row["student_acknowledged_at"],
        "review_requested_at": row["review_requested_at"],
        "updated_at": row["updated_at"],
        "notes": json.loads(row["notes_json"]) if row["notes_json"] else None,
        "evidence": evidence_out,
        "payment_confirmations": [dict(pr) for pr in payments],
        "legacy_rewards_row": dict(legacy) if legacy else None,
    }


def list_payment_confirmations(
    *,
    conn: sqlite3.Connection,
    reward_id: str | None = None,
    student_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List payment confirmations without raw Stripe JSON (operator-safe summaries)."""
    where_clauses: list[str] = []
    params: list[Any] = []

    if reward_id is not None:
        where_clauses.append("reward_id=?")
        params.append(reward_id)

    if student_id is not None:
        where_clauses.append("student_id=?")
        params.append(student_id)

    if status is not None:
        where_clauses.append("status=?")
        params.append(status)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    params.append(limit)
    params.append(offset)

    rows = conn.execute(
        f"""
        SELECT id, stripe_event_id, stripe_payment_intent_id, reward_id, student_id,
               status, applied_at, provenance, created_at
        FROM payment_confirmations
        WHERE {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()

    return [dict(r) for r in rows]


def acknowledge_reward(
    *,
    conn: sqlite3.Connection,
    reward_id: str,
    student_id: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Apply student acknowledgement evidence and transition reward state.

    Returns:
      dict with "ok", "error", "current_state", or "transition" keys.
    """
    row = _load_reward_row(conn, reward_id)
    if not row:
        return {"error": "reward_not_found"}

    current_state = RewardState(str(row["state"]))
    ledger_student_id = str(row["student_id"])

    # Always validate student_id first
    if ledger_student_id != student_id:
        insert_support_signal(
            conn=conn,
            kind="ack_student_mismatch",
            payload={
                "reward_id": reward_id,
                "request_student_id": student_id,
                "ledger_student_id": ledger_student_id,
            },
        )
        return {
            "error": "ack_student_mismatch",
            "current_state": current_state.value,
        }

    # Idempotent: already acknowledged is ok
    if current_state is RewardState.STUDENT_ACKNOWLEDGED:
        return {"ok": True, "already_acknowledged": True}

    if current_state is not RewardState.PAYMENT_CONFIRMED:
        return {
            "error": "ack_requires_payment_confirmed",
            "current_state": current_state.value,
        }

    append_evidence(
        conn=conn,
        student_id=student_id,
        session_id=None,
        reward_id=reward_id,
        evidence_type=EvidenceType.STUDENT_CONFIRMATION,
        payload={"notes": notes} if notes else {},
        provenance="ack_api",
    )

    transition = apply_evidence_to_reward(
        conn=conn,
        reward_id=reward_id,
        evidence_type=EvidenceType.STUDENT_CONFIRMATION,
        ingest_payload={"student_ack": True, "notes": notes}
        if notes
        else {"student_ack": True},
    )

    conn.commit()

    result: dict[str, Any] = {"ok": True}
    if transition:
        result["transition"] = {
            "new_state": transition.new_state.value,
            "new_outcome": transition.new_outcome.value,
            "notes": list(transition.notes),
        }
    return result


def create_nudge(
    *,
    conn: sqlite3.Connection,
    student_id: str,
    reward_id: str | None,
    failure_command: str | None,
    suggestion: str,
) -> None:
    now = _utc_now_iso()
    conn.execute(
        """
    INSERT INTO nudges (student_id, reward_id, created_at, failure_command, suggestion)
    VALUES (?, ?, ?, ?, ?)
    """,
        (student_id, reward_id, now, failure_command, suggestion),
    )
    conn.commit()


def _build_where_clause(
    student_id: str | None,
) -> tuple[str, list[Any]]:
    """Return a safe (WHERE clause, params) pair for an optional student_id filter.

    The clause is always one of two hardcoded strings — never interpolated from
    user input — so f-string use below is safe.  Centralising the logic here
    removes the fragile inline pattern and makes the intent explicit.
    """
    if student_id:
        return "WHERE student_id=?", [student_id]
    return "", []


def get_outcome_summary(
    conn: sqlite3.Connection,
    *,
    student_id: str | None = None,
) -> dict[str, Any]:
    where, params = _build_where_clause(student_id)

    cur = conn.execute(
        f"SELECT state, COUNT(*) as cnt FROM reward_ledger {where} GROUP BY state",
        params,
    )
    by_state: dict[str, int] = {}
    total = 0
    for row in cur.fetchall():
        by_state[row["state"]] = row["cnt"]
        total += row["cnt"]

    cur2 = conn.execute(
        f"SELECT COUNT(DISTINCT student_id) as n FROM reward_ledger {where}",
        params,
    )
    student_count = cur2.fetchone()["n"]

    return {
        "total_rewards": total,
        "by_state": by_state,
        "student_count": student_count,
    }


# ---------------------------------------------------------------------------
# Epistemic token helpers
# ---------------------------------------------------------------------------


def _reward_token_to_dict(token: RewardToken) -> dict[str, Any]:
    """Serialize a RewardToken to a JSON-safe dict."""
    return {
        "insight_tier": token.insight_tier.value,
        "base_bank_depth": token.base_bank_depth,
        "inferential_richness": token.inferential_richness,
        "trend_position": token.trend_position,
        "rarity_score": token.rarity_score,
        "issuance_trigger": token.issuance_trigger,
        "issued_at": token.issued_at,
        "amount": token.amount,
    }


def _reward_token_from_dict(d: dict[str, Any]) -> RewardToken:
    """Deserialize a RewardToken from a stored dict."""
    return RewardToken(
        insight_tier=InsightTier(d["insight_tier"]),
        base_bank_depth=int(d["base_bank_depth"]),
        inferential_richness=float(d["inferential_richness"]),
        trend_position=float(d["trend_position"]),
        rarity_score=float(d["rarity_score"]),
        issuance_trigger=str(d["issuance_trigger"]),
        issued_at=str(d["issued_at"]),
    )


def issue_reward_token(
    *,
    conn: sqlite3.Connection,
    reward_id: str,
    token: RewardToken,
) -> dict[str, Any]:
    """Stamp an epistemic RewardToken onto an existing reward row.

    Idempotent by reward_id: if a token is already issued, return it unchanged.
    On first issue, writes reward_token_json and reward_token_amount.
    Returns the serialized token dict on success, or an error key.
    """
    row = _load_reward_row(conn, reward_id)
    if not row:
        return {"error": "reward_not_found"}

    existing_raw = row["reward_token_json"]
    if existing_raw:
        existing_dict = json.loads(existing_raw)
        existing_token = _reward_token_from_dict(existing_dict)
        return {
            "ok": True,
            "reward_id": reward_id,
            "token": _reward_token_to_dict(existing_token),
            "immutable": True,
            "note": "token_already_issued",
        }

    token_dict = _reward_token_to_dict(token)
    conn.execute(
        """
        UPDATE reward_ledger
        SET reward_token_json=?, reward_token_amount=?, updated_at=?
        WHERE reward_id=?
        """,
        (
            json.dumps(token_dict, ensure_ascii=False),
            token.amount,
            _utc_now_iso(),
            reward_id,
        ),
    )
    conn.commit()
    return {"ok": True, "reward_id": reward_id, "token": token_dict}


# ---------------------------------------------------------------------------
# Scope resolution helpers
# ---------------------------------------------------------------------------


def resolve_token_scope(
    *,
    conn: sqlite3.Connection,
    reward_id: str,
) -> dict[str, Any]:
    """Resolve the TokenScope for a reward by inspecting its token and evidence.

    Scope *emerges* from stored data — no separate scope table needed.
    Returns a dict with token_scope and tool_scope if available.
    """
    row = _load_reward_row(conn, reward_id)
    if not row:
        return {"error": "reward_not_found"}

    # -- Token scope (from RewardToken if issued) --
    token_scope_data: dict[str, Any] | None = None
    raw_token = row["reward_token_json"]
    if raw_token:
        token = _reward_token_from_dict(json.loads(raw_token))

        # Find the provenance and evidence_type from the earliest evidence
        # row linked to this reward.
        prov_row = conn.execute(
            "SELECT provenance, evidence_type FROM evidence_ledger "
            "WHERE reward_id=? ORDER BY created_at ASC LIMIT 1",
            (reward_id,),
        ).fetchone()
        provenance = prov_row["provenance"] if prov_row else "unknown"
        evidence_type = (
            EvidenceType(prov_row["evidence_type"])
            if prov_row
            else EvidenceType.GLASS_SESSION_EVENT
        )

        scope = infer_token_scope(
            token=token,
            provenance=provenance,
            evidence_type=evidence_type,
        )
        token_scope_data = {
            "insight_tier": scope.insight_tier.value,
            "rarity_band": scope.rarity_band,
            "issuance_trigger": scope.issuance_trigger,
            "provenance": scope.provenance,
            "evidence_type": scope.evidence_type.value,
        }

    # -- Tool scope (from provenance of first evidence row) --
    tool_scope_data: dict[str, Any] | None = None
    if raw_token:
        tool_scope = ToolScope.from_provenance(provenance)
        if tool_scope:
            tool_scope_data = {
                "provenance": tool_scope.provenance,
                "evidence_type": tool_scope.evidence_type.value,
                "source_system": tool_scope.source_system,
                "produces_transitions": tool_scope.produces_transitions,
                "payload_keys": list(tool_scope.payload_keys),
            }

    return {
        "ok": True,
        "reward_id": reward_id,
        "token_scope": token_scope_data,
        "tool_scope": tool_scope_data,
    }


def resolve_tool_scope(
    *,
    provenance: str,
) -> dict[str, Any]:
    """Resolve the ToolScope for a known provenance string.

    Returns a dict with tool_scope if the provenance is known,
    or a suggestion to register it if unknown.
    """
    tool_scope = ToolScope.from_provenance(provenance)
    if tool_scope:
        return {
            "ok": True,
            "provenance": provenance,
            "known": True,
            "tool_scope": {
                "provenance": tool_scope.provenance,
                "evidence_type": tool_scope.evidence_type.value,
                "source_system": tool_scope.source_system,
                "produces_transitions": tool_scope.produces_transitions,
                "payload_keys": list(tool_scope.payload_keys),
            },
        }
    return {
        "ok": True,
        "provenance": provenance,
        "known": False,
        "note": "Unknown provenance — not an error; new tools add new provenance strings organically.",
    }


# ---------------------------------------------------------------------------
# Exchange request helpers
# ---------------------------------------------------------------------------


def _exchange_result_to_dict(result: ExchangeResult) -> dict[str, Any]:
    """Serialize an ExchangeResult to a JSON-safe dict for storage."""
    return {
        "request_id": result.request_id,
        "approved": result.approved,
        "evaluated_at": result.evaluated_at,
        "final_approved_scope": result.final_approved_scope,
        "layers": [
            {
                "layer": lr.layer.value,
                "passed": lr.passed,
                "approved_scope": lr.approved_scope,
                "blocked_keys": list(lr.blocked_keys),
                "notes": list(lr.notes),
            }
            for lr in result.layers
        ],
    }


def store_exchange_request(
    *,
    conn: sqlite3.Connection,
    request: ExchangeRequest,
    result: ExchangeResult,
    constraint_config_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Persist an exchange request and its evaluation result.

    ON CONFLICT(request_id) DO NOTHING — idempotent by request_id.
    Returns the persisted record summary.
    """
    result_dict = _exchange_result_to_dict(result)
    try:
        conn.execute(
            """
            INSERT INTO exchange_requests (
                request_id, reward_id, student_id, requested_scope_json,
                constraint_config_json, constraint_result_json, approved, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_id) DO NOTHING
            """,
            (
                request.request_id,
                request.reward_id,
                request.student_id,
                json.dumps(request.requested_scope, ensure_ascii=False),
                json.dumps(constraint_config_snapshot, ensure_ascii=False),
                json.dumps(result_dict, ensure_ascii=False),
                1 if result.approved else 0,
                _utc_now_iso(),
            ),
        )
    except sqlite3.IntegrityError:
        return {"duplicate": True, "request_id": request.request_id}
    conn.commit()
    return {
        "ok": True,
        "request_id": request.request_id,
        "reward_id": request.reward_id,
        "approved": result.approved,
        "final_approved_scope": result.final_approved_scope,
        "layers": result_dict["layers"],
    }


def patch_evidence_reward_id(
    *,
    conn: sqlite3.Connection,
    evidence_id: int,
    reward_id: str,
) -> dict[str, Any]:
    """Retroactively associate an evidence row with a reward.

    Evidence recorded without a reward_id (evidence-only path) can be linked
    to a reward row after the fact using this function.

    Returns:
      {"ok": True, "evidence_id": <id>, "reward_id": <id>}  on success
      {"error": "evidence_not_found"}                        if id not in ledger
      {"error": "reward_not_found"}                          if reward_id not in ledger
      {"error": "already_linked", "linked_reward_id": <id>} if row already has a reward_id
    """
    cur = conn.execute(
        "SELECT id, reward_id FROM evidence_ledger WHERE id=?",
        (evidence_id,),
    )
    row = cur.fetchone()
    if not row:
        return {"error": "evidence_not_found"}

    existing_reward = row["reward_id"]
    if existing_reward is not None:
        return {"error": "already_linked", "linked_reward_id": existing_reward}

    reward_row = _load_reward_row(conn, reward_id)
    if not reward_row:
        return {"error": "reward_not_found"}

    conn.execute(
        "UPDATE evidence_ledger SET reward_id=? WHERE id=?",
        (reward_id, evidence_id),
    )
    conn.commit()
    return {"ok": True, "evidence_id": evidence_id, "reward_id": reward_id}


def list_exchange_requests(
    *,
    conn: sqlite3.Connection,
    student_id: str | None = None,
    reward_id: str | None = None,
    approved: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List exchange requests with optional filters."""
    where_clauses: list[str] = []
    params: list[Any] = []

    if student_id is not None:
        where_clauses.append("student_id=?")
        params.append(student_id)

    if reward_id is not None:
        where_clauses.append("reward_id=?")
        params.append(reward_id)

    if approved is not None:
        where_clauses.append("approved=?")
        params.append(1 if approved else 0)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    params.append(limit)
    params.append(offset)

    rows = conn.execute(
        f"""
        SELECT id, request_id, reward_id, student_id,
               requested_scope_json, constraint_result_json, approved, created_at
        FROM exchange_requests
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()

    return [
        {
            "id": row["id"],
            "request_id": row["request_id"],
            "reward_id": row["reward_id"],
            "student_id": row["student_id"],
            "requested_scope": json.loads(row["requested_scope_json"]),
            "constraint_result": json.loads(row["constraint_result_json"]),
            "approved": bool(row["approved"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Session memory — persistent cross-session context carryover
# ---------------------------------------------------------------------------


def store_session_memory(
    *,
    conn: sqlite3.Connection,
    memory_key: str,
    memory_value: str,
    source_path: str,
    scope: str = "x-change",
    session_id: str | None = None,
) -> int:
    """Persist a non-secret context note for cross-session retrieval.

    Stores key-value metadata with source path provenance and freshness
    tracking.  Do not store secrets, raw event payloads, or large blobs.

    Returns the new row id.
    """
    cur = conn.execute(
        """
        INSERT INTO session_memory
          (memory_key, memory_value, source_path, scope, session_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            memory_key,
            memory_value,
            source_path,
            scope,
            session_id,
            _utc_now_iso(),
        ),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def retrieve_session_memory(
    *,
    conn: sqlite3.Connection,
    memory_key: str | None = None,
    scope: str | None = None,
    include_stale: bool = False,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retrieve session memory entries with freshness metadata.

    Excludes stale entries by default.  Every returned row carries
    source_path and created_at so callers can verify provenance and age.
    """
    where_clauses: list[str] = []
    params: list[Any] = []

    if not include_stale:
        where_clauses.append("is_stale = 0")

    if memory_key is not None:
        where_clauses.append("memory_key = ?")
        params.append(memory_key)

    if scope is not None:
        where_clauses.append("scope = ?")
        params.append(scope)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    params.append(limit)

    rows = conn.execute(
        f"""
        SELECT id, memory_key, memory_value, source_path, scope,
               session_id, is_stale, created_at, stale_checked_at
        FROM session_memory
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()

    return [dict(r) for r in rows]


def mark_stale_memory(
    *,
    conn: sqlite3.Connection,
    memory_id: int | None = None,
    memory_key: str | None = None,
) -> bool:
    """Flag a memory entry as stale with a timestamp check.

    Requires at least one of memory_id or memory_key.  If memory_key is
    given and memory_id is not, flags the most recent matching row.

    Returns True if a row was updated, False otherwise.
    """
    if memory_id is None and memory_key is None:
        return False

    now = _utc_now_iso()
    if memory_id is not None:
        cur = conn.execute(
            """
            UPDATE session_memory
            SET is_stale = 1, stale_checked_at = ?
            WHERE id = ?
            """,
            (now, memory_id),
        )
    else:
        # Flags most-recent matching row by key
        cur = conn.execute(
            """
            UPDATE session_memory
            SET is_stale = 1, stale_checked_at = ?
            WHERE id = (
              SELECT id FROM session_memory
              WHERE memory_key = ?
              ORDER BY created_at DESC
              LIMIT 1
            )
            """,
            (now, memory_key),
        )
    conn.commit()
    return cur.rowcount > 0


def get_memory_freshness_report(
    *,
    conn: sqlite3.Connection,
    scope: str | None = None,
) -> dict[str, Any]:
    """Return a count of fresh vs. stale entries, optionally scoped."""
    scope_filter = ""
    params: list[Any] = []
    if scope is not None:
        scope_filter = "WHERE scope = ?"
        params.append(scope)

    cur = conn.execute(
        f"""
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN is_stale = 0 THEN 1 ELSE 0 END) AS fresh,
          SUM(CASE WHEN is_stale = 1 THEN 1 ELSE 0 END) AS stale
        FROM session_memory
        {scope_filter}
        """,
        params,
    )
    row = cur.fetchone()
    return {
        "total": row["total"],
        "fresh": row["fresh"] or 0,
        "stale": row["stale"] or 0,
        "scope": scope,
    }
