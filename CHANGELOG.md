# Unreleased baseline

- Add Python 3.10+ packaging, runtime dependencies, and installed CLI entry point.
- Repair package imports while retaining the original direct-script launch.
- Implement configuration-file loading and CLI/environment precedence.
- Preserve omitted CLI defaults and reject missing/example credentials.
- Add a side-effect-free dry run and nonzero CLI error statuses.
- Remove request exception strings and provider bodies from CLI logs.
- Add offline regression tests, six-job CI, and installed-wheel checks.
- Add honest work-in-progress docs and BSD-2-Clause licensing.
- Provider verification, timeouts, IP-state handling, and logger repairs pending.
