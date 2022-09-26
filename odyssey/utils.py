import re
import requests
import socket
import ssl

from typing import Dict, List, Tuple, Union

from collections import defaultdict
from furl import furl

from odyssey.config.loader import IP_LOGGERS
from odyssey.logger import Logger, LoggerType


def match_ip_logger(
    *data: Tuple[str, str, Union[str, None], Union[str, None]], is_https: bool
) -> Union[str, None]:
    """
    Detects IP loggers in the redirect chain,
    depending on rules defined in the Odyssey
    configuration file.

    Args:
        data (Tuple[str, str, Union[str, None], Union[str, None]]):
            A tuple consisting of the objects accessible,
            in IP logging detection rules.
        is_https (bool):
            A boolean indicating whether HTTPS is used.

    Returns:
        If no rule is matched, None is returned.
        Otherwise, the name of the IP logging service,
        is returned as a string.
    """

    domain = data[0]
    ip = data[1]
    subject_common_name = data[2]
    serial_number = data[3]

    for service in IP_LOGGERS:
        for name, patterns in service.items():
            matchers = [dict(pattern) for pattern in patterns]
            for matcher in matchers:
                matcher_type, matcher_value = matcher.get("match"), matcher.get("value")

                match_results = {
                    "DOMAIN": domain == matcher_value,
                    "IP": ip == matcher_value,
                }

                if is_https:
                    match_results.update(
                        {"SSL_CERT_DOMAIN": subject_common_name == matcher_value}
                    )
                    match_results.update(
                        {"SSL_SERIAL_NUMBER": serial_number == matcher_value}
                    )

                # Supplied matcher type is not supported
                if matcher_type not in match_results.keys():
			return None

                matches = list(filter(match_results.get, match_results))

                if len(matches) == 0:
                    return None
                else:
                    return name


def get_ip_address_information(ip: str) -> Tuple[str, str, str, str, float, float]:
    """
    Gets information about an IP address from the
    ip-api.com API.

    Args:
        ip (str):
            An IP address.

    Returns:
        A tuple containing information about the IP
        address, such as:
            - Country
            - ISP
            - Organization
            - ASN
            - Latitude
            - Longitude
    """

    request = requests.get(f"http://ip-api.com/json/{ip}")
    json_response = request.json()

    return (
        json_response["country"],
        json_response["isp"],
        json_response["org"],
        json_response["as"],
        json_response["lat"],
        json_response["lon"],
    )


def get_ssl_cert_from_url(url) -> Union[Dict[str, Dict[str, str]], None]:
    """
    Tries to obtain & parse the SSL certificate
    of a domain from a given URL.

    Args:
        url (str):
            A URL.

    Returns:
        A tuple containing information about the IP
        address, such as:
            - Country
            - ISP
            - Organization
            - ASN
            - Latitude
            - Longitude
    """

    ssl_certificate = None

    host = furl(url).host
    port = furl(url).port

    context = ssl.SSLContext()
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_default_certs()

    TCP_SOCKET = socket.socket()
    SSL_SOCKET = context.wrap_socket(TCP_SOCKET, server_hostname=host)

    try:
        SSL_SOCKET.connect((host, port))
        ssl_certificate = SSL_SOCKET.getpeercert()
    except Exception as exception:
        print(exception)

    if not ssl_certificate:
        return None

    # Parse SSL certificate into an easy-to-use dictionary
    parsed_ssl_certificate = {}
    used_keys = []

    for key, value in ssl_certificate.items():

        element_dictionary = {}

        if not isinstance(value, tuple):
            parsed_ssl_certificate[key] = value

        else:
            for element in value:
			
                if isinstance(element, tuple):
				
                    parsed_ssl_certificate[key] = element
					
                    if isinstance(element[0], tuple):
                        sub_element = element[0]
                        sub_key, sub_value = sub_element
                        element_dictionary[sub_key] = sub_value
                    else:
                        sub_key, sub_value = element
                        element_dictionary[sub_key] = sub_value
						
                else:
                    used_keys.append(key)
                    parsed_ssl_certificate[key] = element

            if key not in used_keys:
                parsed_ssl_certificate[key] = element_dictionary

    return parsed_ssl_certificate


def get_ip_from_url(url):
    host = furl(url).host
    try:
        ip = socket.gethostbyname(host)
        return ip
    except socket.error as exception:
        Logger().message(
            LoggerType.ERROR,
            __file__,
            f"An unexpected {exception.__class__.__name__} occurred during an attempt to resolve ({host}) to an IP address",
        )
        return


def parse_cookies(cookies: List[str]) -> Dict[str, Dict[str, Dict[str, str]]]:

    cookies_dictionary = {}
    for raw_cookie in cookies:

        cookie_segments = raw_cookie.split("; ")

        cookie = cookie_segments[0]

        cookie_key, cookie_value = cookie.split("=")

        # Anything after the first index are cookie attributes
        cookie_attributes = cookie_segments[1:]

        cookie_attributes_dictionary = {}

        for cookie_attribute in cookie_attributes:
            try:
                key, value = cookie_attribute.split("=")
                cookie_attributes_dictionary[key.lower()] = value
            except ValueError:
                # If a cookie attribute is not the form
                # key=value, default to setting the attribute
                # to an empty string.
                cookie_attributes_dictionary[cookie_attribute.lower()] = ""

        cookies_dictionary[cookie_key] = {
            "value": cookie_value,
            "attributes": cookie_attributes_dictionary,
        }

    return cookies_dictionary


class Headers:
    def __init__(self, headers) -> None:
        """
        Headers class constructor.

        Args:
            headers (List[str]):
                A list of the response headers.
        """
        self.headers = headers

    def _parse_headers(self) -> Dict[str, List[str]]:
        """
        Parses HTTP headers into a dictionary.

        Returns:
            A dictionary containing the parsed HTTP headers.
        """

        parsed_headers = defaultdict(list)

        for header in self.headers:

            key, value = header.split(": ", 1)[0].title(), header.split(": ", 1)[1]

            if key in parsed_headers.keys():
                parsed_headers[key].append(value)
            else:
                parsed_headers[key] = [value]

        return parsed_headers

    def get(self, header_key: str) -> Union[str, List[str], None]:
        """
        Extracts the value of `header_key` from the headers dictionary.

        Args:
            header_key(str):
                Header key to retrieve the corresponding value for.

        Returns:
            If there is no associated header value None will be returned.

            If there is only one occurrence of `header_key`
            or if the `header_key` is `Server` it will return the first
            header value it finds that has the key `header_key`.

            If there is more than one occurrence of `header_key` or
            if the `header_key` is `Set-Cookie` a list of all the
            associated values will be returned.
        """

        header_value = self._parse_headers().get(header_key)

        # Set of header keys that are disregarded if there are multiple occurrences
        # of it in a response it will always take the first one that appears to be
        # the true value of the associated key.
        SELECT_FIRST_OVERRIDE = "Server"

        # Set of header keys that are forced to always return a list.
        ALWAYS_LIST_OVERRIDE = "Set-Cookie"

        if not header_value:
            return None

        if header_key in ALWAYS_LIST_OVERRIDE:
            return header_value

        # Only one occurrence of this header exists
        if len(header_value) == 1 or header_key in SELECT_FIRST_OVERRIDE:
            return header_value[0]

        # Multiple occurrences of this header exist
        #
        # It appears that the RFC7230 specification does not allow for this,
        # however as described in https://github.com/whatwg/html/issues/2900
        # by annevk most browsers treat said header as a comma separated list.
        # Odyssey should also handle this like the aforementioned browsers.
        #
        # RFC7230 Specification: https://www.rfc-editor.org/rfc/rfc7230#section-3.2.2
        elif len(header_value) >= 2:
            return header_value

    def dump(self) -> Dict[str, List[str]]:
        """
        Returns the parsed HTTP headers dictionary,
        for convenience sake.

        Returns:
            A dictionary containing the parsed HTTP headers.
        """
        return self._parse_headers()
