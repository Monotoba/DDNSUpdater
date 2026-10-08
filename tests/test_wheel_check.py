import importlib.util
import os
from pathlib import Path


def test_entry_point_found_outside_python_directory(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'scripts' / 'check_wheel.py'
    spec = importlib.util.spec_from_file_location('wheel_check', source)
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    prefix = tmp_path / 'python-install'
    commands = prefix / 'Scripts'
    commands.mkdir(parents=True)
    name = 'namecheap-ddns.exe' if os.name == 'nt' else 'namecheap-ddns'
    executable = commands / name
    executable.write_text('test command sentinel')
    executable.chmod(0o755)
    monkeypatch.setattr(check.sys, 'executable', str(prefix / 'python.exe'))
    monkeypatch.setattr(check.sysconfig, 'get_path', lambda name: str(commands))
    monkeypatch.setenv('PATH', '')
    assert Path(check.installed_entry_point()) == executable
