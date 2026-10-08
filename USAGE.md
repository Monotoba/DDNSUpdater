# DDNSUpdater usage

This is a work-in-progress tool. Use `--dry-run` for configuration validation
before attempting a real update. Offline tests cover the update flow; live
provider behavior has not yet been validated.

## Commands

After installation, run `namecheap-ddns --help` or `python -m ddns_updater --help`.
Existing short options remain available: `-d`, `-hs`, `-lf`, and `-ip`.

| Option | Purpose | Default |
| --- | --- | --- |
| `--domain` | Domain to update | Required |
| `--host` | Record host/subdomain | `@` |
| `--log-file` | XML log path | `test.log` |
| `--ip-file` | IP-state path | `last_ip.txt` |
| `--config-file` | Optional INI settings | None |
| `--dry-run` | Validate without requests or file writes | Off |

The Dynamic DNS password is required through `DDNS_API_PASSWORD` or an existing
configuration file. There is no CLI password argument. The password is never
printed by the dry run. Example domain/password values are rejected.

## Configuration

```ini
[Settings]
domain = YOUR_DOMAIN
host = YOUR_HOST
log_file = ddns.log
ip_file = last_ip.txt
```

```sh
namecheap-ddns --config-file config.ini --dry-run
```

CLI options override matching INI values; INI values override defaults.
`DDNS_API_PASSWORD`, when present, overrides the legacy `api_password` INI field.
A blank environment value is rejected rather than falling back to a stored key.
Passwords containing `%` are read literally. Missing or malformed configuration
files fail before requests or logger creation; partial settings files are allowed
when the remaining required values are supplied elsewhere.

For compatibility, `api_password` in `[Settings]` is supported, but plaintext
secret files should be protected and excluded from Git. Prefer environment
configuration. Relative paths resolve from the current working directory.

## Exit behavior and limitations

- Exit 0: dry-run settings are valid, or provider XML confirms the requested IPv4
  update and the state file is saved. This does not verify DNS propagation.
- Exit 2: invalid CLI/configuration.
- Exit 1: discovery, provider, state-file, or logging failure. A state/log failure
  can occur after DNS has changed; rerun after correcting the file problem.

The updater does not run a scheduler or daemon. Unattended scheduling should wait
for controlled live validation. Discovery uses `https://api4.ipify.org`;
the provider receives the exact discovered IPv4 in an encoded HTTPS GET. Both
requests disable redirects and use 5-second connect / 15-second read timeouts.
These are Requests timeouts, not a total wall-clock deadline. IPv6 and malformed
addresses are rejected. Provider XML must contain one `ErrCount` of `0`, one
`Done` of `true`, and a matching `IP`; error entries and malformed XML fail.

The state file retains the original `IP @ timestamp` format. It is replaced
atomically only after provider confirmation; save failures propagate to exit 1.
Its parent directory must already exist. This file is a success record, not a
cache: each invocation sends an update. No automatic retries are performed.
No live DNS update was validated.

## XML logging

The logger writes UTF-8 XML with one entry per successful log call. Existing
entries are retained across runs, and each write atomically replaces the log.
Malformed XML, an unexpected root, unsupported document types, or invalid UTF-8
fail before the CLI sends requests. Preserve or move the damaged file for
diagnosis, then select a new log path; the tool does not silently erase it.

Runtime log-read/write failures return exit 1. Failed entries are not replayed
on later calls. Explicit logger `exception()` and `trace()` methods retain
diagnostic details, so callers should not pass secrets to those methods. The
DDNS CLI uses generic error messages and does not log provider bodies or request
exception details.

Default timestamps use UTC. The CLI enables the local timezone and records its
current numeric offset (including half-hour/quarter-hour zones). The logger
`set_timezone()` method overrides the displayed local-zone label only; it does
not select a different timezone or change the local offset.

Use one writer per log/state path. Atomic replacement prevents partially written
files but does not serialize overlapping runs. Logs are read and rewritten as
one XML document and have no automatic rotation; their size grows over time.
Parent directories must exist and permit creation/replacement of files.

Only Requests is a third-party runtime dependency; argparse, configparser, and
XML utilities are included with Python. No live update is needed to run tests.
