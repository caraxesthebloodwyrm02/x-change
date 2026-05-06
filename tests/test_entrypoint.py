from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import xchange.__main__ as entrypoint


class MainEntrypointTests(unittest.TestCase):
    def test_main_uses_default_host_and_port(self) -> None:
        # patch.dict restores the original env on exit, even after manual pops
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XCHANGE_HOST", None)
            os.environ.pop("XCHANGE_PORT", None)
            with patch.object(entrypoint, "run_server") as mock_run:
                entrypoint.main()
                mock_run.assert_called_once_with(host="0.0.0.0", port=8788)

    def test_main_respects_env_vars(self) -> None:
        overrides = {"XCHANGE_HOST": "127.0.0.1", "XCHANGE_PORT": "9001"}
        with patch.dict(os.environ, overrides):
            with patch.object(entrypoint, "run_server") as mock_run:
                entrypoint.main()
                mock_run.assert_called_once_with(host="127.0.0.1", port=9001)


if __name__ == "__main__":
    unittest.main()
