# DDNSUpdater v0.1.0a1 — experimental alpha

Prepared release notes. GitHub publication is pending; PyPI publication is on hold.

A Python 3.10+ command-line tool for updating a Namecheap dynamic-DNS IPv4 record.
This initial alpha is intended for evaluation and contributor feedback. It is
not recommended for unattended or production use. No live DNS update or DNS
propagation check has been performed for this release.

## Included

- Installable wheel and source archive with the `namecheap-ddns` command.
- Module launchers and the original direct-script launch path.
- CLI/config/environment precedence, required-setting checks, and dry-run validation.
- HTTPS IPv4 discovery, encoded provider parameters, connect/read timeouts, and
  provider XML verification against the requested IP.
- Atomic state/log writes; state is saved after provider confirmation.
- XML logger repairs, Unicode handling, and local timezone offset formatting.
- BSD-2-Clause license, usage and contributor docs, badges, and offline regression tests.

## Install and evaluate

Once published, download the wheel from this GitHub prerelease, activate a
Python 3.10+ virtual environment, and run:

```sh
python -m pip install ./monotoba_ddnsupdater-0.1.0a1-py3-none-any.whl
namecheap-ddns --help
```

Set `DDNS_API_PASSWORD` in the process environment to your Dynamic DNS password,
then use `namecheap-ddns --domain YOUR_DOMAIN --host YOUR_HOST --dry-run`.
Dry runs validate configuration only. They do not contact Namecheap, validate
credentials, discover an IP, or write files. See [USAGE.md](USAGE.md).

## Known limitations

- Real-service behavior and DNS propagation remain unvalidated.
- IPv4 only; no scheduler, daemon, retries, or change-detection cache.
- Requests use 5-second connect / 15-second read timeouts, not a total deadline.
- One writer per log/state path; overlapping runs are not serialized.
- Logs grow over time and have no automatic rotation.
- A state/log failure can occur after DNS changes; a nonzero exit does not prove
  the DNS record was unchanged.
- Existing malformed logs are preserved and block updates until a new valid
  log path is selected. Parent directories must already exist.
- CI covers Python 3.10 and 3.12 on Linux, Windows, and Intel macOS. Native ARM
  environments and other Python versions are not part of this validation matrix.
- PyPI publication remains on hold.

## Feedback

Open an issue with OS, Python version, expected/actual behavior, and sanitized
reproduction steps. Do not include passwords, provider response bodies, or
password-bearing URLs. Controlled live testing on a dedicated test record is a
priority for contributors; do not send real updates from tests or CI.
