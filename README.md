# DDNSUpdater

[![Tests](https://github.com/Monotoba/DDNSUpdater/actions/workflows/tests.yml/badge.svg)](https://github.com/Monotoba/DDNSUpdater/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-work%20in%20progress-orange)
[![License](https://img.shields.io/badge/license-BSD--2--Clause-blue)](LICENSE)

A small Python command-line tool intended to update a Namecheap dynamic-DNS
record. Useful for a home server or another service whose public IP changes.

**Work in progress — not ready for unattended use.** Installation, CLI settings,
configuration files, and credential-safe error messages have an offline test
baseline. HTTPS IPv4 discovery, connect/read timeouts, provider XML verification,
and atomic state saving are implemented. Logger correctness still needs repairs
before release.
No live DNS update has been validated. PyPI publication remains on hold.

## Install from the checkout

Requires Python 3.10+. Create and activate a virtual environment, then:

```sh
git clone https://github.com/Monotoba/DDNSUpdater.git
cd DDNSUpdater
python -m pip install -e ".[test]"
namecheap-ddns --help
```

`python -m ddns_updater` and `python -m ddns_updater.ddns_updater` also work.
The original `python ddns_updater/ddns_updater.py` launch path is retained.

## Start with a dry run

Set `DDNS_API_PASSWORD` in the process environment to your **Dynamic DNS
password**, then validate settings:

```sh
namecheap-ddns --domain YOUR_DOMAIN --host YOUR_HOST --dry-run
```

Dry runs validate configuration only: they do not check credentials against
Namecheap, send requests, or write log/IP files. Never post your password in
issues or commit a credentials file. For file format and precedence, see
[USAGE.md](USAGE.md).

Omitting `--dry-run` runs the unfinished update flow and can change a DNS record.
The flow checks provider XML and saves state only after confirmed success.
Use the dry run while remaining logger and live-validation work is completed.

## Cleanup steps

1. **Implemented:** install metadata, command/module entry points, CLI/config
   precedence, defaults, required-setting checks, dry run, and offline tests/CI.
2. **Implemented:** verify provider responses; validate IPv4 addresses; add HTTPS
   discovery and timeouts; atomically save state after confirmed success.
3. **Next:** fix logger duplicate entries and file errors with regression tests.
4. GitHub description/topics and baseline built-artifact checks are complete.
   Publish an explicitly labeled alpha when the remaining blockers are resolved.

Contributors can help with mocked provider responses and cross-platform checks.
See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [BSD-2-Clause](LICENSE).
