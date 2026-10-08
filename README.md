# DDNSUpdater

[![Tests](https://github.com/Monotoba/DDNSUpdater/actions/workflows/tests.yml/badge.svg)](https://github.com/Monotoba/DDNSUpdater/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/Monotoba/DDNSUpdater?include_prereleases)](https://github.com/Monotoba/DDNSUpdater/releases/tag/v0.1.0a1)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-experimental%20alpha-orange)
[![License](https://img.shields.io/badge/license-BSD--2--Clause-blue)](LICENSE)

A small Python command-line tool intended to update a Namecheap dynamic-DNS
record. Useful for a home server or another service whose public IP changes.

**Experimental alpha — not ready for unattended use.** Installation, CLI settings,
configuration files, and credential-safe error messages have an offline test
baseline. HTTPS IPv4 discovery, connect/read timeouts, provider XML verification,
and atomic state saving are implemented. XML logging writes each message once,
preserves corrupt logs, and reports file failures.
Version **0.1.0a1** is available as a [GitHub prerelease](https://github.com/Monotoba/DDNSUpdater/releases/tag/v0.1.0a1). No live DNS update has been validated. PyPI publication remains on hold.
See [RELEASE_NOTES.md](RELEASE_NOTES.md) for scope and known limitations.

## Install the alpha

Requires Python 3.10+. Create and activate a virtual environment, then download
the wheel from the [GitHub prerelease](https://github.com/Monotoba/DDNSUpdater/releases/tag/v0.1.0a1) and install it locally:

```sh
python -m pip install ./monotoba_ddnsupdater-0.1.0a1-py3-none-any.whl
namecheap-ddns --help
```

For contributors, install from the checkout:

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

Omitting `--dry-run` sends an experimental update request and can change a DNS record.
The flow checks provider XML and saves state only after confirmed success.
Start with a dry run. A controlled live provider update is still needed to
validate real-service behavior before recommending unattended use.

## Cleanup steps

1. **Implemented:** install metadata, command/module entry points, CLI/config
   precedence, defaults, required-setting checks, dry run, and offline tests/CI.
2. **Implemented:** verify provider responses; validate IPv4 addresses; add HTTPS
   discovery and timeouts; atomically save state after confirmed success.
3. **Implemented:** repair logger duplicate entries, atomic file saving,
   malformed-log handling, and fractional-hour timezone formatting.
4. GitHub description/topics and baseline built-artifact checks are complete.
   The initial experimental alpha is published with a wheel, source archive,
   and checksums. Stable/unattended-use claims require a controlled live provider check.

Contributors can help with mocked provider responses and cross-platform checks.
See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [BSD-2-Clause](LICENSE).
