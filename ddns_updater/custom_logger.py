import logging
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
import traceback
from datetime import datetime, timezone
import tempfile
from pathlib import Path


class CustomLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # Fail early on an inaccessible path without keeping an unused file handle.
        with open(log_file, "a", encoding="utf-8"):
            pass
        self._read_existing_log()
        self.xml_root = ET.Element("log")
        self.timestamp_format = "%Y-%m-%d %H:%M:%S %Z"
        self.system_timezone = self._get_system_timezone()
        self.use_system_timezone_flag = False
        self._timezone_label_override = None

        # Define a custom logging level for EXCEPTION and TRACE
        self.EXCEPTION = 35
        self.TRACE = 36
        logging.addLevelName(self.EXCEPTION, "EXCEPTION")
        logging.addLevelName(self.TRACE, "TRACE")

    def set_timestamp_format(self, format_str):
        self.timestamp_format = format_str

    def set_timezone(self, timezone):
        self.system_timezone = timezone
        self._timezone_label_override = timezone

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
        log_entry = ET.Element(log_level)
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

        self.xml_root.append(log_entry)
        try:
            self._write_to_log_file()
        finally:
            # Never replay a successful or failed message on the next log call.
            self.xml_root.clear()

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
            local = now.astimezone()
            label = self._timezone_label_override or self._format_offset(local.utcoffset())
            # A named fixed offset preserves local wall time and makes %Z reliable.
            local = local.replace(tzinfo=timezone(local.utcoffset(), name=label))
            return local.strftime(self.timestamp_format)
        return now.strftime(self.timestamp_format)

    @staticmethod
    def _format_offset(offset):
        minutes = int(offset.total_seconds() / 60)
        hours, remainder = divmod(abs(minutes), 60)
        sign = '-' if minutes < 0 else '+'
        return f'UTC{sign}{hours:02d}:{remainder:02d}'

    def _get_system_timezone(self):
        return self._format_offset(datetime.now(timezone.utc).astimezone().utcoffset())

    def _get_formatted_exception(self):
        exception_info = traceback.format_exc()

        if exception_info.strip() == "NoneType: None":
            exception_info = "No Exception Found!"

        return exception_info.strip()

    def _get_formatted_trace(self):
        stack_trace = traceback.format_stack()
        return "".join(stack_trace)

    def _read_existing_log(self):
        target = Path(self.log_file)
        existing_content = target.read_text(encoding='utf-8').strip() if target.exists() else ''
        # Preserve corrupt logs for diagnosis instead of silently discarding history.
        if '<!DOCTYPE' in existing_content.upper():
            raise ValueError('XML log document types are not supported.')
        root = ET.fromstring(existing_content) if existing_content else ET.Element('log')
        if root.tag != 'log':
            raise ValueError('Existing XML log has an unexpected root element.')
        return root

    def _write_to_log_file(self):
        target = Path(self.log_file)
        existing_root = self._read_existing_log()
        for log_entry in self.xml_root:
            existing_root.append(log_entry)

        content = self._get_pretty_xml_string(existing_root)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=target.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None and os.path.exists(temporary):
                os.unlink(temporary)

    def _get_pretty_xml_string(self, element):
        # Discard only formatting whitespace; leave message/traceback text intact.
        for node in element.iter():
            if len(node) and node.text and not node.text.strip():
                node.text = None
            if node.tail and not node.tail.strip():
                node.tail = None
        rough_string = ET.tostring(element, encoding='utf-8')
        parsed_xml = xml.dom.minidom.parseString(rough_string)
        try:
            return parsed_xml.toprettyxml(indent='  ', newl='\n')
        finally:
            parsed_xml.unlink()

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
