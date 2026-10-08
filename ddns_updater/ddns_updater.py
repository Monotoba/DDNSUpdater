#!/usr/bin/env python
"""
This script updates the NameCheap dynamic DNS (DDNS) service.

It retrieves the external IP address, stores it in a file, and
updates the DDNS using the provided arguments or a config file.

Usage:
    python ddns_updater.py [--domain DOMAIN] [--host HOST] [--log-file LOG_FILE] [--ip-file IP_FILE]

"""

import argparse
import configparser
import datetime
import os
import ipaddress
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

import requests

if __package__:
    from .custom_logger import CustomLogger
else:
    from custom_logger import CustomLogger


class DDNSUpdater:
    """
    DDNSUpdater is responsible for updating a NameCheap dynamic DNS (DDNS) service.

    Args:
        logger (CustomLogger): An instance of CustomLogger for logging.
        config_file (str, optional): Path to the config file. Defaults to None.
        host (str, optional): Host/subdomain to update. Defaults to "@".
        domain (str, optional): Domain name for DDNS update. Required before updating.
        api_password (str, optional): Dynamic DNS password. Required before updating.
        ip_file (str, optional): Name of the file to store the last IP address. Defaults to "last_ip.txt".
        log_file (str, optional): Name of the log file. Defaults to "test.log".
    """

    def __init__(self, logger, config_file=None, host: str = "@", domain: str = None,
                 api_password: str = None, ip_file="last_ip.txt", log_file: str = "test.log"):
        self.domain = domain
        self.host = host
        self.log_file = log_file
        self.ip_file = ip_file
        self.api_password = api_password
        self.logger = logger

        self.config = configparser.ConfigParser(interpolation=None)
        if config_file:
            with open(config_file, encoding='utf-8') as stream:
                self.config.read_file(stream)
            for key in ('domain', 'host', 'api_password', 'log_file', 'ip_file'):
                value = self.read_config_value('Settings', key)
                if value is not None:
                    setattr(self, key, value)


    def read_config_value(self, section, key):
        """
        Reads a value from the config file.

        Args:
            section (str): Section name in the config file.
            key (str): Key name in the specified section.

        Returns:
            str: The value from the config file, or None if the section or key is not found.
        """
        return self.config.get(section, key, fallback=None)

    def validate_configuration(self):
        for field in ('domain', 'host', 'api_password', 'ip_file', 'log_file'):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'Missing required setting: {field}.')
        if self.domain == 'example.com' or self.api_password == '1234567890':
            raise ValueError('Replace example domain/password values before updating.')

    @staticmethod
    def validate_ipv4(value):
        """Require an IPv4 address before sending it to the provider."""
        try:
            return str(ipaddress.IPv4Address(value.strip()))
        except (ValueError, AttributeError):
            raise ValueError('Invalid IPv4 address.') from None

    def get_external_ip_address(self):
        """Discover IPv4 over HTTPS with connect/read timeouts."""
        response = requests.get('https://api4.ipify.org', timeout=(5, 15),
                                allow_redirects=False)
        if response.status_code != 200:
            raise ValueError('IP discovery did not return HTTP 200.')
        return self.validate_ipv4(response.text)

    def store_last_ip(self, ip_address):
        """Atomically replace state after a confirmed provider update."""
        ip_address = self.validate_ipv4(ip_address)
        now = datetime.datetime.now().strftime('%m/%d/%Y - %H:%M:%S')
        target = Path(self.ip_file)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=target.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(f'{ip_address} @ {now}\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None and os.path.exists(temporary):
                os.unlink(temporary)

    def update_ddns(self, ip_address=None):
        """Send an encoded HTTPS GET and require an explicit XML success."""
        self.validate_configuration()
        if ip_address is None:
            ip_address = self.get_external_ip_address()
        ip_address = self.validate_ipv4(ip_address)
        response = requests.get(
            'https://dynamicdns.park-your-domain.com/update',
            params={'host': self.host, 'domain': self.domain,
                    'password': self.api_password, 'ip': ip_address},
            timeout=(5, 15), allow_redirects=False)
        if response.status_code != 200:
            raise ValueError('Provider did not return HTTP 200.')
        # Do not reflect provider text: it can contain credentials or HTML errors.
        if len(response.content) > 65536 or '<!DOCTYPE' in response.text.upper():
            raise ValueError('Invalid provider response.')
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            raise ValueError('Invalid provider XML.') from None
        def field(name):
            nodes = root.findall(name)
            return nodes[0].text.strip() if len(nodes) == 1 and nodes[0].text else None
        if (root.tag != 'interface-response' or field('ErrCount') != '0'
                or field('Done') != 'true' or field('IP') != ip_address
                or root.findall('./Errors/*') or root.findall('./errors/*')):
            raise ValueError('Provider did not confirm the requested IPv4 update.')
        return response.text.strip()


def main(argv=None):
    """Run one update, or validate configuration without network activity."""
    parser = argparse.ArgumentParser(description="Namecheap Dynamic DNS Updater (work in progress)")
    parser.add_argument("--domain", "-d", help="Domain name for DDNS update")
    parser.add_argument("--host", "-hs", help="Host/subdomain (default: @)")
    parser.add_argument("--log-file", "-lf", help="Log file (default: test.log)")
    parser.add_argument("--ip-file", "-ip", help="IP file (default: last_ip.txt)")
    parser.add_argument("--config-file", help="INI file with a [Settings] section")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate settings without network requests or file writes")
    args = parser.parse_args(argv)

    try:
        updater = DDNSUpdater(None, config_file=args.config_file)
    except (OSError, configparser.Error, UnicodeError):
        parser.error("Could not read configuration file; check its path and INI format.")
    for key in ('domain', 'host', 'log_file', 'ip_file'):
        value = getattr(args, key)
        if value is not None:
            setattr(updater, key, value)
    if 'DDNS_API_PASSWORD' in os.environ:
        updater.api_password = os.environ['DDNS_API_PASSWORD']
    try:
        updater.validate_configuration()
    except ValueError as error:
        parser.error(str(error))

    if args.dry_run:
        print('Configuration valid. No network requests or files written.')
        return 0

    try:
        logger = CustomLogger(updater.log_file)
        logger.use_system_timezone(True)
        updater.logger = logger
    except OSError:
        print('Could not open log file; check its path and permissions.', file=sys.stderr)
        return 1
    try:
        external_ip = updater.get_external_ip_address()
        updater.update_ddns(external_ip)
        updater.store_last_ip(external_ip)
        logger.info('Provider confirmed the IPv4 update; IP state saved.')
        return 0
    except Exception:
        # Request exception strings can include the password-bearing URL.
        message = 'DDNS update or state saving failed. Check configuration, connectivity, and file permissions.'
        print(message, file=sys.stderr)
        try:
            logger.error(message)
        except Exception:
            # Logging must not leak a chained password-bearing request exception.
            pass
        return 1


if __name__ == '__main__':
    sys.exit(main())
