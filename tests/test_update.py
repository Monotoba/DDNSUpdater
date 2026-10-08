from unittest.mock import Mock

import pytest
import requests

from ddns_updater import ddns_updater as module

IP = '198.51.100.7'
SUCCESS = f'<interface-response><IP>{IP}</IP><ErrCount>0</ErrCount><Errors/><Done>true</Done></interface-response>'


def response(body=SUCCESS, status=200):
    return Mock(status_code=status, text=body, content=body.encode())


@pytest.fixture
def updater():
    return module.DDNSUpdater(Mock(), domain='my-domain.test', api_password='a%&?#secret')


def test_discovery_https_timeout_and_ipv4(monkeypatch, updater):
    get = Mock(return_value=response('  ' + IP + '\n'))
    monkeypatch.setattr(module.requests, 'get', get)
    assert updater.get_external_ip_address() == IP
    get.assert_called_once_with('https://api4.ipify.org', timeout=(5, 15), allow_redirects=False)


@pytest.mark.parametrize('body', ['::1', 'hello', '', '999.1.1.1', '198.51.100.7\n198.51.100.8'])
def test_invalid_discovery_rejected(monkeypatch, updater, body):
    monkeypatch.setattr(module.requests, 'get', Mock(return_value=response(body)))
    with pytest.raises(ValueError):
        updater.get_external_ip_address()


@pytest.mark.parametrize('status', [301, 403, 500])
def test_discovery_non_200_rejected(monkeypatch, updater, status):
    monkeypatch.setattr(module.requests, 'get', Mock(return_value=response(IP, status)))
    with pytest.raises(ValueError):
        updater.get_external_ip_address()


def test_provider_receives_exact_discovered_ip_and_encoded_params(monkeypatch, updater):
    get = Mock(return_value=response())
    monkeypatch.setattr(module.requests, 'get', get)
    assert updater.update_ddns(IP) == SUCCESS
    get.assert_called_once_with('https://dynamicdns.park-your-domain.com/update',
        params={'host': '@', 'domain': 'my-domain.test', 'password': 'a%&?#secret', 'ip': IP},
        timeout=(5, 15), allow_redirects=False)
    prepared = requests.Request('GET', get.call_args.args[0], params=get.call_args.kwargs['params']).prepare()
    assert 'password=a%25%26%3F%23secret' in prepared.url


@pytest.mark.parametrize('body', ['<html>secret</html>', 'not XML', '',
    SUCCESS.replace('<ErrCount>0', '<ErrCount>1'),
    SUCCESS.replace('<Done>true', '<Done>false'),
    SUCCESS.replace(IP, '198.51.100.8'),
    SUCCESS.replace('<Errors/>', '<Errors><Err1>secret</Err1></Errors>'),
    SUCCESS.replace('<Errors/>', '<errors><Err1>secret</Err1></errors>'),
    SUCCESS.replace('<Done>true</Done>', ''),
    SUCCESS.replace('<ErrCount>0</ErrCount>', '<ErrCount>0</ErrCount><ErrCount>0</ErrCount>'),
    '<!DOCTYPE interface-response>' + SUCCESS,
    'x' * 65537], ids=['html', 'invalid-xml', 'empty', 'provider-error',
        'not-done', 'wrong-ip', 'upper-errors', 'lower-errors', 'missing-done',
        'duplicate-count', 'doctype', 'oversized'])
def test_provider_rejection_is_sanitized(monkeypatch, updater, body):
    monkeypatch.setattr(module.requests, 'get', Mock(return_value=response(body)))
    with pytest.raises(ValueError) as error:
        updater.update_ddns(IP)
    assert 'secret' not in str(error.value)


@pytest.mark.parametrize('status', [302, 401, 500])
def test_provider_http_errors_rejected(monkeypatch, updater, status):
    monkeypatch.setattr(module.requests, 'get', Mock(return_value=response(status=status)))
    with pytest.raises(ValueError):
        updater.update_ddns(IP)


def test_invalid_ip_fails_before_request(updater):
    with pytest.raises(ValueError):
        updater.update_ddns('::1')


def test_direct_update_discovers_ip(monkeypatch, updater):
    get = Mock(side_effect=[response(IP), response()])
    monkeypatch.setattr(module.requests, 'get', get)
    updater.update_ddns()
    assert get.call_count == 2
    assert get.call_args.kwargs['params']['ip'] == IP


def test_state_replaced_and_temp_removed(updater, tmp_path):
    path = tmp_path / updater.ip_file
    path.write_text('old state')
    updater.store_last_ip(IP)
    assert path.read_text().startswith(IP + ' @ ')
    assert list(tmp_path.iterdir()) == [path]


def test_failed_replace_preserves_state(monkeypatch, updater, tmp_path):
    path = tmp_path / updater.ip_file
    path.write_text('old state')
    monkeypatch.setattr(module.os, 'replace', Mock(side_effect=OSError('disk error')))
    with pytest.raises(OSError):
        updater.store_last_ip(IP)
    assert path.read_text() == 'old state'
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('failure', ['discovery', 'provider', 'state', 'logging', None])
def test_cli_order_and_failure_status(monkeypatch, tmp_path, capsys, failure):
    monkeypatch.setenv('DDNS_API_PASSWORD', 'private-password')
    logger = Mock()
    monkeypatch.setattr(module, 'CustomLogger', lambda *args: logger)
    calls = []
    def discover(self):
        calls.append('discovery')
        if failure == 'discovery':
            raise requests.Timeout('private-password')
        return IP
    def update(self, ip):
        assert ip == IP
        calls.append('provider')
        if failure == 'provider':
            raise requests.RequestException('private-password')
    def save(self, ip):
        calls.append('state')
        if failure == 'state':
            raise OSError('private-password')
    monkeypatch.setattr(module.DDNSUpdater, 'get_external_ip_address', discover)
    monkeypatch.setattr(module.DDNSUpdater, 'update_ddns', update)
    monkeypatch.setattr(module.DDNSUpdater, 'store_last_ip', save)
    if failure == 'logging':
        logger.info.side_effect = OSError('private-password')
        logger.error.side_effect = OSError('private-password')
    assert module.main(['--domain', 'my-domain.test']) == (0 if failure is None else 1)
    expected = ['discovery'] if failure == 'discovery' else ['discovery', 'provider'] if failure == 'provider' else ['discovery', 'provider', 'state']
    assert calls == expected
    captured = capsys.readouterr()
    assert 'private-password' not in captured.out + captured.err + str(logger.mock_calls)


@pytest.mark.parametrize('encoding', ['utf-8', 'utf-16'])
def test_provider_utf16_declaration_with_decoded_text(monkeypatch, updater, encoding):
    body = '<?xml version="1.0" encoding="utf-16"?>' + SUCCESS.replace('<Errors/>', '<errors/>')
    result = response(body)
    result.content = body.encode(encoding)
    monkeypatch.setattr(module.requests, 'get', Mock(return_value=result))
    assert updater.update_ddns(IP) == body
