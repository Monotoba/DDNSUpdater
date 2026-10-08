"""Check installed entry points outside the checkout without sending DNS updates."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

wheels = list(Path('dist').glob('*.whl'))
if len(wheels) != 1:
    raise RuntimeError('Expected exactly one freshly built wheel.')
subprocess.run([sys.executable, '-m', 'pip', 'install', '--force-reinstall',
                '--no-deps', str(wheels[0].resolve())], check=True)
env = dict(os.environ, DDNS_API_PASSWORD='offline-wheel-check-password')
env.pop('PYTHONPATH', None)
with tempfile.TemporaryDirectory() as directory:
    commands = [
        [sys.executable, '-m', 'ddns_updater', '--help'],
        [sys.executable, '-m', 'ddns_updater.ddns_updater', '--help'],
        [sys.executable, '-m', 'ddns_updater', '--domain', 'offline.test', '--dry-run'],
    ]
    entry = shutil.which('namecheap-ddns', path=str(Path(sys.executable).parent))
    if entry is None:
        raise RuntimeError('Installed console entry point was not found.')
    commands.append([entry, '--domain', 'offline.test', '--dry-run'])
    for command in commands:
        subprocess.run(command, cwd=directory, env=env, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if list(Path(directory).iterdir()):
        raise RuntimeError('Help/dry-run commands unexpectedly created files.')
print('Installed wheel entry-point and dry-run checks passed')
