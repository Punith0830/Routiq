"""Privacy setup for pinned CrewAI 1.15.27 in this dedicated local module."""
import os
import threading
from pathlib import Path

_lock = threading.Lock()
_prepared = False


def prepare_runtime(root: Path):
    global _prepared
    with _lock:
        if _prepared:
            return
        os.environ["CREWAI_TRACING_ENABLED"] = "false"
        os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
        os.environ["CREWAI_DISABLE_TRACKING"] = "true"
        os.environ["OTEL_SDK_DISABLED"] = "true"
        os.environ["CREWAI_STORAGE_DIR"] = str((root / ".coach-runtime").resolve())
        # This release probes AMP credentials during import even with tracing
        # disabled. This application does not use AMP. Deny that probe before
        # importing CrewAI so it cannot read/write unrelated credential storage.
        import crewai_core.auth.token as token

        def no_amp_credentials():
            raise token.AuthError("AMP is disabled for Routiq")

        token.get_auth_token = no_amp_credentials
        _prepared = True
