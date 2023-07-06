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

import requests

from custom_logger import CustomLogger


class DDNSUpdater:
    """
    DDNSUpdater is responsible for updating a NameCheap dynamic DNS (DDNS) service.

    Args:
        logger (CustomLogger): An instance of CustomLogger for logging.
        config_file (str, optional): Path to the config file. Defaults to None.
        host (str, optional): Host/subdomain to update. Defaults to "@".
        domain (str, optional): Domain name for DDNS update. Defaults to "example.com".
        api_password (str, optional): API password for the DDNS service. Defaults to "1234567890".
        ip_file (str, optional): Name of the file to store the last IP address. Defaults to "last_ip.txt".
        log_file (str, optional): Name of the log file. Defaults to "test.log".
    """

    def __init__(self, logger, config_file=None, host: str = "@", domain: str = "example.com",
                 api_password: str = "1234567890", ip_file="last_ip.txt", log_file: str = "test.log"):
        self.domain = domain
        self.host = host
        self.log_file = log_file
        self.ip_file = ip_file
        self.api_password = api_password
        self.logger = logger

        self.config = configparser.ConfigParser()
        if config_file:
            self.config.read(config_file)

    def read_config_value(self, section, key):
        """
        Reads a value from the config file.

        Args:
            section (str): Section name in the config file.
            key (str): Key name in the specified section.

        Returns:
            str: The value from the config file, or None if the section or key is not found.
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.logger("")
            return None

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
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve external IP address: {str(e)}")
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
        url = f"https://dynamicdns.park-your-domain.com/update?host={self.host}&domain={self.domain}&password={self.api_password}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update DDNS: {str(e)}")
            raise


def main():
    """
    Entry point of the script.
    """
    parser = argparse.ArgumentParser(description="NameCheap Dynamic DNS Updater")
    parser.add_argument("--domain", "-d", help="Domain name for DDNS update")
    parser.add_argument("--host", "-hs", help="Host/subdomain to update")
    parser.add_argument("--log-file", "-lf", help="Log file name")
    parser.add_argument("--ip-file", "-ip", help="IP file name")
    args = parser.parse_args()

    logfile = args.log_file if args.log_file else "test.log"
    logger = CustomLogger(logfile)
    logger.use_system_timezone(True)
    updater = DDNSUpdater(logger, config_file=None)

    updater.domain = args.domain
    updater.host = args.host
    updater.log_file = args.log_file
    updater.ip_file = args.ip_file
    updater.api_password = os.environ.get('DDNS_API_PASSWORD')

    # Perform the DDNS update
    try:
        external_ip = updater.get_external_ip_address()
        updater.store_last_ip(external_ip)
        response = updater.update_ddns()
        logger.info(f"DDNS update response: {response}")
    except Exception as e:
        logger.error(f"An error occurred during DDNS update: {str(e)}")


if __name__ == '__main__':
    main()
