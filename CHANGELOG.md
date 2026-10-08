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
- Write XML log entries once without retaining unused file handlers.
- Atomically save logs and preserve malformed/invalid-UTF-8 logs for diagnosis.
- Fail before network requests when the existing log cannot be read or parsed.
- Correct negative fractional-hour offsets and refresh local offsets per entry.
- Cover real-logger CLI integration with mocked provider responses.
- Live provider validation remains pending; no release has been published.
