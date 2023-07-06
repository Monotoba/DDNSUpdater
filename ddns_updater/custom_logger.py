import logging
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
import traceback
from datetime import datetime, timezone
import re


class CustomLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler(log_file))
        self.xml_root = ET.Element("log")
        self.timestamp_format = "%Y-%m-%d %H:%M:%S %Z"
        self.system_timezone = self._get_system_timezone()
        self.use_system_timezone_flag = False

        # Define a custom logging level for EXCEPTION and TRACE
        self.EXCEPTION = 35
        self.TRACE = 36
        logging.addLevelName(self.EXCEPTION, "EXCEPTION")
        logging.addLevelName(self.TRACE, "TRACE")

    def set_timestamp_format(self, format_str):
        self.timestamp_format = format_str

    def set_timezone(self, timezone):
        self.system_timezone = timezone

    def get_timezone(self):
        return self.system_timezone

    def use_system_timezone(self, use_system=True):
        self.use_system_timezone_flag = use_system

    def debug(self, message):
        self._log(message, logging.DEBUG)

    def info(self, message):
        self._log(message, logging.INFO)

    def warning(self, message):
        self._log(message, logging.WARNING)

    def error(self, message):
        self._log(message, logging.ERROR)

    def exception(self, message):
        self._log(message, self.EXCEPTION, log_exception=True)

    def trace(self, message):
        self._log(message, self.TRACE, log_trace=True)

    def critical(self, message):
        self._log(message, logging.CRITICAL)

    def _log(self, message, level, log_exception=False, log_trace=False):
        log_level = self._get_log_level(level)
        log_entry = ET.SubElement(self.xml_root, log_level)
        timestamp = ET.SubElement(log_entry, "timestamp")
        timestamp.text = self._get_timestamp()
        log_message = ET.SubElement(log_entry, "message")
        log_message.text = message
        if log_exception:
            exception_info = self._get_formatted_exception()
            traceback_elem = ET.SubElement(log_entry, "traceback")
            traceback_elem.text = exception_info
        if log_trace:
            trace_info = self._get_formatted_trace()
            trace_elem = ET.SubElement(log_entry, "execution")
            trace_elem.text = trace_info

        self._write_to_log_file()

    def _get_log_level(self, level):
        if level == logging.DEBUG:
            return "debug"
        elif level == logging.INFO:
            return "info"
        elif level == logging.WARNING:
            return "warning"
        elif level == logging.ERROR:
            return "error"
        elif level == logging.CRITICAL:
            return "critical"
        elif level == self.EXCEPTION:
            return "exception"
        elif level == self.TRACE:
            return "trace"
        else:
            return "unknown"

    def _get_timestamp(self):
        now = datetime.now(timezone.utc)

        if self.use_system_timezone_flag:
            timestamp = now.astimezone().strftime(self.timestamp_format)
            return timestamp.replace("UTC", self.system_timezone, 1)
        else:
            return now.strftime(self.timestamp_format)

    def _get_system_timezone(self):
        now = datetime.now()
        offset = now.astimezone().strftime("%z")
        hours = int(offset) // 100
        minutes = int(offset) % 100
        return f"UTC{hours:+03d}:{minutes:02d}"

    def _get_formatted_exception(self):
        exception_info = traceback.format_exc()

        if exception_info.strip() == "NoneType: None":
            exception_info = "No Exception Found!"

        return exception_info.strip()

    def _get_formatted_trace(self):
        stack_trace = traceback.format_stack()
        return "".join(stack_trace)

    def _write_to_log_file(self):
        existing_content = ""
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as file:
                existing_content = file.read().strip()

        if existing_content:
            try:
                existing_tree = ET.ElementTree(ET.fromstring(existing_content))
                existing_root = existing_tree.getroot()
            except ET.ParseError:
                existing_root = None
        else:
            existing_root = None

        # Create a new XML root element if it doesn't exist
        if existing_root is None:
            existing_root = ET.Element("log")

        #self.remove_spaces_from_xml(existing_root)

        # Add the new log entries to the existing root element
        for log_entry in self.xml_root:
            existing_root.append(log_entry)

        # Write the XML log file with pretty printing
        with open(self.log_file, "w") as file:
            file.write(self._get_pretty_xml_string(existing_root))

    def _get_pretty_xml_string(self, element):
        rough_string = ET.tostring(element, encoding="utf-8")
        parsed_xml = xml.dom.minidom.parseString(rough_string)

        # Remove leading/trailing whitespace
        pretty_xml = parsed_xml.toprettyxml(indent="", newl="").strip()
        # Add a single new line after each element
        #pretty_xml = re.sub(r">\s*<", "><", pretty_xml)
        pretty_xml = parsed_xml.toprettyxml(indent="  ", newl="\n")

        return pretty_xml


    def remove_spaces_from_xml(self, xml_content):
        # Parse the XML content
        root = ET.fromstring(xml_content)

        # Remove spaces and new lines between elements
        self.remove_spaces_newlines_recursive(root)

        # Generate the XML string without spaces and new lines
        xml_string = ET.tostring(root, encoding="unicode", method="xml")

        return xml_string

    def remove_spaces_newlines_recursive(self, element):
        # Remove spaces and new lines between elements
        if element.tail:
            element.tail = element.tail.strip()

        # Recursively remove spaces and new lines from child elements
        for child in element:
            self.remove_spaces_newlines_recursive(child)


if __name__ == '__main__':
    logger = CustomLogger("test.log")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.use_system_timezone(True)
    logger.info("We are now using the system timezone")
    logger.use_system_timezone(False)
    logger.info("We are now using the default UTC timezone")
    logger.exception("An exception occurred")
    logger.trace("This is a trace message")
    logger.critical("This is a critical message")
