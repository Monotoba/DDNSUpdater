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

    def get_external_ip_address(self):
        """
        Retrieves the external IP address.

        Returns:
            str: The external IP address.

        Raises:
            requests.exceptions.RequestException: If there is an error retrieving the IP address.
        """
        try:
            response = requests.get("http://ipecho.net/plain")
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException:
            self.logger.error("Failed to retrieve external IP address.")
            raise

    def store_last_ip(self, ip_address):
        """
        Stores the last IP address in a file.

        Args:
            ip_address (str): The IP address to store.
        """
        now = datetime.datetime.now().strftime('%m/%d/%Y - %H:%M:%S')
        line = f"{ip_address} @ {now}\n"
        try:
            with open(self.ip_file, 'w') as file:
                file.write(line)
        except IOError as e:
            self.logger.error(f"Failed to store last IP address: {str(e)}")

    def update_ddns(self):
        """
        Updates the DDNS.

        Returns:
            str: The response from the DDNS update.

        Raises:
            requests.exceptions.RequestException: If there is an error updating the DDNS.
        """
        self.validate_configuration()
        url = f"https://dynamicdns.park-your-domain.com/update?host={self.host}&domain={self.domain}&password={self.api_password}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException:
            self.logger.error("Failed to update DDNS.")
            raise


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
        updater.store_last_ip(external_ip)
        updater.update_ddns()
        logger.info('DDNS request returned HTTP success; provider response is not yet validated.')
        return 0
    except Exception:
        # Request exception strings can include the password-bearing URL.
        logger.error('DDNS update failed. Check configuration, connectivity, and file permissions.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
