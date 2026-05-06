from __future__ import annotations

import hashlib
import hmac
import time
from typing import Final


# Stripe uses: https://stripe.com/docs/webhooks/signatures#verify-signatures
#
# Header format:
#   t=149999... , v1= 888... , v0= 777...
#
# We require a v1 match.
#
# This is strict fail-closed when the secret is missing.

_MAX_REASONABLE_TIMESTAMP_AGE_SECONDS: Final[int] = 300


def _parse_signature_header(header_value: str) -> dict[str, str]:
  parts = [p.strip() for p in header_value.split(",")]
  out: dict[str, str] = {}
  for p in parts:
    if "=" not in p:
      continue
    k, v = p.split("=", 1)
    out[k.strip()] = v.strip()
  return out


def verify_stripe_signature(
  *,
  payload_body: bytes,
  sig_header: str | None,
  stripe_secret: str | None,
  tolerance_seconds: int,
) -> bool:
  if not stripe_secret:
    return False
  if not sig_header:
    return False

  sig = _parse_signature_header(sig_header)
  t = sig.get("t")
  if not t:
    return False

  try:
    t_int = int(t)
  except ValueError:
    return False

  now = int(time.time())
  if abs(now - t_int) > tolerance_seconds:
    return False

  # Stripe signs: "{t}.{payload_body}"
  signed_payload = f"{t}.".encode("utf-8") + payload_body

  their_sig = sig.get("v1")
  if not their_sig:
    return False

  digest = hmac.new(
    stripe_secret.encode("utf-8"),
    signed_payload,
    hashlib.sha256,
  ).hexdigest()
  return hmac.compare_digest(digest, their_sig)
