from __future__ import annotations

import os

from xchange.main import run_server


def main() -> None:
  host = os.environ.get("XCHANGE_HOST", "0.0.0.0")
  port = int(os.environ.get("XCHANGE_PORT", "8788"))
  run_server(host=host, port=port)


if __name__ == "__main__":
  main()

