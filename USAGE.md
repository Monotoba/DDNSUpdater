# DDNSUpdater usage

This is a work-in-progress tool. Use `--dry-run` for configuration validation
until the update-flow blockers in [README.md](README.md) are resolved.

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

- Exit 0: dry-run settings are valid, or the current update flow returns HTTP
  success. This does **not yet confirm provider-level DNS update success**.
- Exit 2: invalid CLI/configuration.
- Exit 1: runtime update failure or inability to open the log file.

The updater does not run a scheduler or daemon. Unattended scheduling should wait
for response validation, bounded requests, and reliable IP-state persistence.
The current IP-file method logs write failures rather than propagating them;
logger issues and this failure path are pending repairs.

Only Requests is a third-party runtime dependency; argparse, configparser, and
XML utilities are included with Python. No live update is needed to run tests.
