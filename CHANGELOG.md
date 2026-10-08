# Unreleased baseline

- Add Python 3.10+ packaging, runtime dependencies, and installed CLI entry point.
- Repair package imports while retaining the original direct-script launch.
- Implement configuration-file loading and CLI/environment precedence.
- Preserve omitted CLI defaults and reject missing/example credentials.
- Add a side-effect-free dry run and nonzero CLI error statuses.
- Remove request exception strings and provider bodies from CLI logs.
- Add offline regression tests, six-job CI, and installed-wheel checks.
- Add honest work-in-progress docs and BSD-2-Clause licensing.
- Add HTTPS IPv4 discovery and connect/read timeouts with redirects disabled.
- Encode provider parameters and verify XML success against the requested IPv4.
- Save IP state atomically after provider confirmation; propagate save failures.
- Keep runtime errors sanitized even when error logging fails.
- Logger duplicate-entry repairs and live provider validation remain pending.
