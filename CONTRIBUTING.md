# Contributing

Install a Python 3.10+ virtual environment and run:

```sh
python -m pip install -e ".[test]" build
python -m pytest -q
python -m build
python scripts/check_wheel.py
```

Tests prohibit real HTTP requests and use temporary files. Mock responses for
all DNS/IP-discovery tests; never depend on real credentials or change DNS from
CI. Add regression tests for every code change and keep patches focused.

The wheel check runs help and dry-run commands outside the checkout with a dummy
password; it must not make requests or create local state. Report sanitized
errors and reproduction steps without passwords or password-bearing URLs.

The next priorities are duplicate-log repairs and controlled live validation.
Provider, IPv4, timeout, and state-ordering behavior now has offline tests.
No release is ready yet.

CI covers Python 3.10/3.12 on Linux, Windows, and macOS 15 Intel. The explicit
macOS label avoids the current ARM runner capacity delays; native ARM validation
is not part of this baseline matrix. Review the label when GitHub retires it.
