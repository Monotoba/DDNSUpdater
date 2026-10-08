from datetime import datetime, timedelta, timezone
import logging
import xml.etree.ElementTree as ET
from unittest.mock import Mock

import pytest

from ddns_updater import custom_logger as module
from ddns_updater import ddns_updater as cli


def entries(path):
    return ET.parse(path).getroot()


def test_each_entry_written_once_across_calls_and_instances(tmp_path):
    path = tmp_path / 'log.xml'
    logger = module.CustomLogger(path)
    for index in range(10):
        logger.info(f'entry {index}')
        assert len(logger.xml_root) == 0
    module.CustomLogger(path).warning('next instance')
    assert [entry.findtext('message') for entry in entries(path)] == [
        *(f'entry {i}' for i in range(10)), 'next instance']
    assert len(list(tmp_path.iterdir())) == 1
    assert '\n\n' not in path.read_text()


def test_no_file_handlers_added_or_left_open(tmp_path):
    shared = logging.getLogger(module.__name__)
    before = list(shared.handlers)
    for i in range(5):
        module.CustomLogger(tmp_path / f'{i}.xml')
    assert shared.handlers == before


@pytest.mark.parametrize('method', ['debug', 'info', 'warning', 'error', 'critical', 'exception', 'trace'])
def test_levels_unicode_and_xml_escaping(tmp_path, method):
    path = tmp_path / 'log.xml'
    logger = module.CustomLogger(path)
    message = '  café Ω <value> & "quote"\nsecond line  '
    getattr(logger, method)(message)
    root = entries(path)
    assert len(root) == 1
    assert root[0].tag == method
    assert root[0].findtext('message') == message
    assert root[0].findtext('timestamp')
    if method == 'exception':
        assert root[0].findtext('traceback') == 'No Exception Found!'
    if method == 'trace':
        assert 'test_levels_unicode_and_xml_escaping' in root[0].findtext('execution')


def test_exception_details_are_preserved_for_explicit_exception_logging(tmp_path):
    path = tmp_path / 'log.xml'
    logger = module.CustomLogger(path)
    try:
        raise RuntimeError('diagnostic')
    except RuntimeError:
        logger.exception('caught')
    assert 'RuntimeError: diagnostic' in entries(path)[0].findtext('traceback')


@pytest.mark.parametrize('contents', ['<log>broken', '<unexpected/>', '<!DOCTYPE log><log/>', b'\xff'])
def test_invalid_existing_log_preserved_at_initialization(tmp_path, contents):
    path = tmp_path / 'log.xml'
    raw = contents if isinstance(contents, bytes) else contents.encode()
    path.write_bytes(raw)
    with pytest.raises((ET.ParseError, ValueError, UnicodeError)):
        module.CustomLogger(path)
    assert path.read_bytes() == raw


@pytest.mark.parametrize('failure', ['replace', 'fsync', 'serialize', 'read'])
def test_failed_write_preserves_history_and_does_not_replay(monkeypatch, tmp_path, failure):
    path = tmp_path / 'log.xml'
    logger = module.CustomLogger(path)
    logger.info('previous')
    before = path.read_bytes()
    with monkeypatch.context() as patch:
        if failure in ('replace', 'fsync'):
            patch.setattr(module.os, failure, Mock(side_effect=OSError('disk error')))
        elif failure == 'serialize':
            patch.setattr(logger, '_get_pretty_xml_string', Mock(side_effect=ValueError('invalid text')))
        else:
            patch.setattr(logger, '_read_existing_log', Mock(side_effect=OSError('read failure')))
        with pytest.raises((OSError, ValueError)):
            logger.error('failed entry')
    assert path.read_bytes() == before
    assert len(logger.xml_root) == 0
    assert list(tmp_path.iterdir()) == [path]
    logger.info('later')
    assert [entry.findtext('message') for entry in entries(path)] == ['previous', 'later']


def test_corruption_after_initialization_not_overwritten(tmp_path):
    path = tmp_path / 'log.xml'
    logger = module.CustomLogger(path)
    path.write_text('corrupt')
    with pytest.raises(ET.ParseError):
        logger.info('new')
    assert path.read_text() == 'corrupt'
    assert len(logger.xml_root) == 0


def test_missing_parent_fails_early(tmp_path):
    with pytest.raises(OSError):
        module.CustomLogger(tmp_path / 'missing' / 'log.xml')


@pytest.mark.parametrize(('minutes', 'expected'), [(330, 'UTC+05:30'), (-210, 'UTC-03:30'),
    (345, 'UTC+05:45'), (-30, 'UTC-00:30'), (0, 'UTC+00:00')])
def test_fractional_timezone_offsets(minutes, expected):
    assert module.CustomLogger._format_offset(timedelta(minutes=minutes)) == expected


def fake_datetime(monkeypatch, minutes):
    zone = timezone(timedelta(minutes=minutes))
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
            return value if tz else value.replace(tzinfo=None)
        def astimezone(self, tz=None):
            return super().astimezone(zone if tz is None else tz)
    monkeypatch.setattr(module, 'datetime', FixedDatetime)


def test_utc_local_and_custom_label_formats(monkeypatch, tmp_path):
    fake_datetime(monkeypatch, -210)
    logger = module.CustomLogger(tmp_path / 'log.xml')
    assert logger.get_timezone() == 'UTC-03:30'
    assert logger._get_timestamp() == '2026-01-15 12:00:00 UTC'
    logger.use_system_timezone(True)
    assert logger._get_timestamp() == '2026-01-15 08:30:00 UTC-03:30'
    logger.set_timezone('Custom label')
    logger.set_timestamp_format('%H:%M %Z %z')
    assert logger._get_timestamp() == '08:30 Custom label -0330'
    logger.use_system_timezone(False)
    assert logger._get_timestamp() == '12:00 UTC +0000'


def test_local_offset_refreshes_for_each_timestamp(monkeypatch, tmp_path):
    fake_datetime(monkeypatch, -420)
    logger = module.CustomLogger(tmp_path / 'log.xml')
    logger.use_system_timezone(True)
    fake_datetime(monkeypatch, -360)
    assert logger._get_timestamp() == '2026-01-15 06:00:00 UTC-06:00'


@pytest.mark.parametrize('contents', ['broken XML', '<unexpected/>', '<!DOCTYPE log><log/>', b'\xff'])
def test_cli_bad_log_fails_before_network(monkeypatch, tmp_path, capsys, contents):
    monkeypatch.setenv('DDNS_API_PASSWORD', 'private-password')
    path = tmp_path / 'log.xml'
    raw = contents if isinstance(contents, bytes) else contents.encode()
    path.write_bytes(raw)
    assert cli.main(['--domain', 'my-domain.test', '--log-file', str(path)]) == 1
    assert path.read_bytes() == raw
    assert not (tmp_path / 'last_ip.txt').exists()
    assert 'XML format' in capsys.readouterr().err


def test_cli_complete_flow_with_real_logger_and_mocked_network(monkeypatch, tmp_path):
    monkeypatch.setenv('DDNS_API_PASSWORD', 'a%&?#private-password')
    ip = '198.51.100.7'
    def response(body):
        return Mock(status_code=200, content=body.encode(), text=body)
    good = f'<interface-response><IP>{ip}</IP><ErrCount>0</ErrCount><errors/><Done>true</Done></interface-response>'
    get = Mock(side_effect=[response(ip), response(good), response(ip), response(good)])
    monkeypatch.setattr(cli.requests, 'get', get)
    for _ in range(2):
        assert cli.main(['--domain', 'my-domain.test']) == 0
    root = entries(tmp_path / 'test.log')
    assert len(root) == 2
    assert [node.tag for node in root] == ['info', 'info']
    assert 'private-password' not in (tmp_path / 'test.log').read_text()
    assert (tmp_path / 'last_ip.txt').read_text().startswith(ip + ' @ ')
    assert get.call_count == 4
