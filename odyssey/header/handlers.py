import ipaddress
import re
import socket

from typing import Dict, List, Union

from collections import defaultdict
from furl import furl

from odyssey.logger import Logger, LoggerType


class HeaderHandlers:
    @staticmethod
    def _handle_location_header(header: str) -> Union[str, None]:
        """
        Parse & validate the value of the `Location` header.

        Args:
            header (str):
                A `Location` header.

        Returns:
            If None is returned, no value was identified.

            Otherwise, a string representing the value of
            the `Location` header will be returned.
        """

        location = None

        parsed_location_header = furl(header)

        parsed_location_header_host = parsed_location_header.host

        # If there is no domain in the URI found in the location header
        if not parsed_location_header_host:
            location = header if header.startswith("/") else "/" + header
        else:

            host_ip_address = None

            IPV4_REGEX = re.compile(
                "^(([1-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
            )

            if re.match(IPV4_REGEX, parsed_location_header_host):
                host_ip_address = parsed_location_header_host
            else:
                # Appears location header does not include an IP, must be a domain.
                # Try and resolve the provided domain to an IP
                try:
                    host_ip_address = str(
                        socket.gethostbyname(parsed_location_header_host)
                    )
                except socket.gaierror as exception:
                    Logger().message(
                        LoggerType.ERROR,
                        __file__,
                        f"Could not resolve {parsed_location_header_host} to an IP address",
                    )
                    return

            # Checks if the domain or ip provided by the location header are routeable
            if host_ip_address and ipaddress.ip_address(host_ip_address).is_global:
                location = header

        return location

    def handle_location_headers(self, headers: List[str]) -> Union[str, None]:
        """
        Handles all `Location` headers identified.

        Args:
            headers (List[str]):
                A list of `Location` headers.

        Returns:
            If no `Location` value can be identified,
            None is returned.

            Otherwise, the last identified `Location`
            header value will be returned.
        """

        locations = []

        for header in headers:
            locations.append(self._handle_location_header(header))

        # If no Location header values were identified.
        if not locations:
            return None
        else:
            return locations[-1]

    @staticmethod
    def _handle_refresh_header(header: str) -> Union[Dict[str, float], None]:
        """
        Parse & validate the value of the `Refresh` header.

        Args:
            header (str):
                A `Refresh` header.

        Returns:
            If the value of the `Refresh` header does not
            match a certain regular expression pattern,
            None is returned.

            Otherwise, a dictionary of the refresh URI
            and TTR (time-to-reload) will be returned.
        """

        refresh_dict = {}

        # Excluding specific character in regular expression
        # Reference: https://stackoverflow.com/a/1409170
        REFRESH_HEADER_RE = re.compile(
            "(?P<ttr>[0-9]+);(url=)?(?P<uri>[^,]+)", re.IGNORECASE
        )
        matches = re.finditer(REFRESH_HEADER_RE, header)

        if not matches:
            return None

        for match in matches:
            ttr, uri = match.group("ttr"), match.group("uri")
            refresh_dict[uri] = float(ttr)

        return refresh_dict

    def handle_refresh_headers(self, headers: List[str]) -> Union[str, None]:
        """
        Handles all `Refresh` headers identified.

        Args:
            headers (List[str]):
                A list of `Refresh` headers.

        Returns:
            If no `Refresh` headers can be identified,
            None will be returned.

            Otherwise, the URI with the shortest
            TTR (time-to-reload) will be returned.
        """

        refresh_dict = {}

        if len(headers) == 1:
            refresh_dict = self._handle_refresh_header(headers[0])

        # Handle multiple occurrences of the same header accordingly.
        elif len(headers) >= 2:

            for header in headers:
                refresh_dict.update(self._handle_refresh_header(header))

        sorted_refresh_dict = defaultdict(list)

        for key, value in refresh_dict.items():
            if value not in sorted_refresh_dict:
                sorted_refresh_dict[value] = [key]
            else:
                sorted_refresh_dict[value].append(key)

        if not sorted_refresh_dict:
            return None

        minimum_ttr = min(sorted_refresh_dict, key=float)
        return sorted_refresh_dict.get(minimum_ttr)[-1]
