from unittest.mock import Mock

import pytest
import requests

from ddns_updater import ddns_updater as module


@pytest.fixture()
def config(tmp_path):
    path = tmp_path / 'config.ini'
    path.write_text('[Settings]\ndomain = my-domain.test\nhost = home\n'
                    'api_password = config%password\nlog_file = configured.log\n'
                    'ip_file = configured-ip.txt\n')
    return path


def test_config_loaded_and_missing_option_safe(config):
    updater = module.DDNSUpdater(Mock(), config_file=config)
    assert updater.domain == 'my-domain.test'
    assert updater.host == 'home'
    assert updater.api_password == 'config%password'
    assert updater.read_config_value('Absent', 'key') is None
    assert updater.read_config_value('Settings', 'absent') is None


def test_dry_run_has_no_side_effects(config, capsys):
    before = set(config.parent.iterdir())
    assert module.main(['--config-file', str(config), '--dry-run']) == 0
    assert set(config.parent.iterdir()) == before
    assert 'No network requests or files written' in capsys.readouterr().out


@pytest.mark.parametrize('field', ['domain', 'host', 'api_password', 'ip_file', 'log_file'])
def test_blank_settings_rejected(field):
    updater = module.DDNSUpdater(Mock(), domain='my-domain.test', api_password='test-password')
    setattr(updater, field, ' ')
    with pytest.raises(ValueError, match=field):
        updater.validate_configuration()


@pytest.mark.parametrize('args', [[], ['--domain', 'my-domain.test'],
                                  ['--domain', 'example.com']])
def test_incomplete_cli_fails_before_network(args, monkeypatch):
    monkeypatch.setenv('DDNS_API_PASSWORD', '' if len(args) == 2 else 'test-password')
    with pytest.raises(SystemExit) as error:
        module.main(args + ['--dry-run'])
    assert error.value.code == 2


@pytest.mark.parametrize('contents', [None, 'not an INI file', '[Settings]\napi_password = secret\nsecret'])
def test_bad_config_is_sanitized(tmp_path, contents, capsys):
    path = tmp_path / 'bad.ini'
    if contents is not None:
        path.write_text(contents)
    with pytest.raises(SystemExit) as error:
        module.main(['--config-file', str(path), '--dry-run'])
    assert error.value.code == 2
    assert 'secret' not in capsys.readouterr().err


def test_cli_and_environment_override_config(config, monkeypatch):
    calls = []
    logger = Mock()
    monkeypatch.setattr(module, 'CustomLogger', lambda path: calls.append(path) or logger)
    def get_ip(self):
        calls.append((self.domain, self.host, self.ip_file, self.api_password))
        return '198.51.100.7'
    monkeypatch.setattr(module.DDNSUpdater, 'get_external_ip_address', get_ip)
    monkeypatch.setattr(module.DDNSUpdater, 'store_last_ip', lambda *args: None)
    monkeypatch.setattr(module.DDNSUpdater, 'update_ddns', lambda *args: 'response')
    monkeypatch.setenv('DDNS_API_PASSWORD', 'environment-password')
    assert module.main(['--config-file', str(config), '--domain', 'override.test',
                        '--host', '@', '--log-file', 'override.log',
                        '--ip-file', 'override-ip.txt']) == 0
    assert calls == ['override.log', ('override.test', '@', 'override-ip.txt', 'environment-password')]


def test_omitted_cli_paths_keep_defaults(monkeypatch):
    calls = []
    monkeypatch.setenv('DDNS_API_PASSWORD', 'test-password')
    monkeypatch.setattr(module, 'CustomLogger', lambda path: calls.append(path) or Mock())
    def get_ip(self):
        calls.append((self.host, self.ip_file))
        return '198.51.100.7'
    monkeypatch.setattr(module.DDNSUpdater, 'get_external_ip_address', get_ip)
    monkeypatch.setattr(module.DDNSUpdater, 'store_last_ip', lambda *args: None)
    monkeypatch.setattr(module.DDNSUpdater, 'update_ddns', lambda *args: '')
    assert module.main(['--domain', 'my-domain.test']) == 0
    assert calls == ['test.log', ('@', 'last_ip.txt')]


def test_request_errors_never_log_secret(monkeypatch):
    logger = Mock()
    monkeypatch.setenv('DDNS_API_PASSWORD', 'private-password')
    monkeypatch.setattr(module, 'CustomLogger', lambda *args: logger)
    monkeypatch.setattr(module.DDNSUpdater, 'get_external_ip_address', lambda *args: '198.51.100.7')
    monkeypatch.setattr(module.DDNSUpdater, 'store_last_ip', lambda *args: None)
    def fail(*args, **kwargs):
        raise requests.RequestException('https://provider.test/?password=private-password')
    monkeypatch.setattr(module.requests, 'get', fail)
    assert module.main(['--domain', 'my-domain.test']) == 1
    assert 'private-password' not in str(logger.mock_calls)


def test_log_open_failure_returns_nonzero(monkeypatch, capsys):
    monkeypatch.setenv('DDNS_API_PASSWORD', 'test-password')
    def fail(*args):
        raise OSError('detail')
    monkeypatch.setattr(module, 'CustomLogger', fail)
    assert module.main(['--domain', 'my-domain.test']) == 1
    assert 'Could not open log file' in capsys.readouterr().err


def test_ip_discovery_http_error_is_sanitized(monkeypatch):
    logger = Mock()
    updater = module.DDNSUpdater(logger)
    def fail(*args, **kwargs):
        raise requests.RequestException('private network detail')
    monkeypatch.setattr(module.requests, 'get', fail)
    with pytest.raises(requests.RequestException):
        updater.get_external_ip_address()
    assert 'private network detail' not in str(logger.mock_calls)


def test_help_requires_no_credentials(capsys):
    with pytest.raises(SystemExit) as error:
        module.main(['--help'])
    assert error.value.code == 0
    assert '--config-file' in capsys.readouterr().out
