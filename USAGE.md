# NameCheap Dynamic DNS (DDNS) Updater

## Introduction
This Python script automates the process of updating the NameCheap Dynamic DNS (DDNS) service. It retrieves the external IP address, stores it in a file, and updates the DDNS using either command-line arguments or a configuration file.

## Usage
To use this script, follow the steps below:

1. Clone the repository or download the script file `ddns_updater.py`.

2. Install the required dependencies by running the following command:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the script with the desired options. Here are some examples:

..Update DDNS using command-line arguments:
   ```Python
  python ddns_updater.py --domain example.com --host subdomain --log-file ddns.log --ip-file last_ip.txt
   ```

..Update DDNS using a configuration file (config.ini):
   ```Python
  python ddns_updater.py --config-file config.ini
   ```

Note: If no log file or IP file is provided, default values will be used.

4. The script will retrieve the external IP address, store it in the specified IP file, and update the 
DDNS service. The log messages will be recorded in the specified log file.

## Configuration File Format
If you choose to use a configuration file, it should be in the INI format. Here's an example configuration file (config.ini):
```Ini
[Settings]
domain = example.com
host = subdomain
api_password = 1234567890
log_file = ddns.log
ip_file = last_ip.txt
```

You can customize the values for the domain, host, API password, log file, and IP file as per your requirements.

## Requirements
- Python 3.x
- Requests library
- configparser library
- xml.etree.ElementTree library
- xml.dom.minidom library

Make sure to install the dependencies using the provided requirements.txt file.

## Conclusion
Automating the NameCheap DDNS update process with this Python script simplifies the management of dynamic IP addresses for your domain. By regularly updating the DDNS, your domain will always be associated with the correct IP address, ensuring seamless access to your hosted services.

Feel free to use and modify the code to suit your specific needs. If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

Happy DDNS updating!
