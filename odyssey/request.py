from typing import Tuple, Union

from furl import furl

from odyssey.config.loader import SEGMENT_BUFFER, USER_AGENT
from odyssey.logger import Logger, LoggerType

import socket
import ssl


class Request:
    def __init__(self, url: str, timeout: int) -> None:
        """
        Request class constructor.

        Args:
            url (str):
                A Uniform Resource Locator (URL).
            timeout (int):
                The amount of seconds a socket should timeout after.
        """
        self.url = url
        self.timeout = timeout

    def execute(self) -> Tuple[Union[bytes, None], str]:
        """
        Sends a HTTP GET request to the URL parsed in the constructor.

        Returns:
            If None is returned, no response was received.

            Otherwise, a byte string is returned containing the
            response body.
        """

        # Standard TCP socket
        TCP_SOCKET = socket.socket()

        parsed_url = furl(self.url)

        scheme = str(parsed_url.scheme)
        domain = str(parsed_url.host)
        port = int(parsed_url.port)
        path = str(parsed_url.path) if str(parsed_url.path) else '/'

        extension = ""

        # Append query to path
        if parsed_url.query:
            path += "?" + str(parsed_url.query)

        # Append fragment to extension
        if parsed_url.fragment:
            extension += "#" + str(parsed_url.fragment)

        IS_HTTPS = scheme == "https"

        REQUEST_SOCKET = (
            ssl.SSLContext().wrap_socket(TCP_SOCKET, server_hostname=domain)
            if IS_HTTPS
            else TCP_SOCKET
        )

        try:
            REQUEST_SOCKET.connect((domain, port))
        except Exception as error:
            Logger().message(
                LoggerType.ERROR,
                __file__,
                f"An unexpected {error.__class__.__name__} occurred during an attempt to connect to ({domain}:{port})",
            )
            return

        data = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {domain}\r\n"
            f"Accept: */*\r\n"
            f"Connection: close\r\n"
            f"User-Agent: {USER_AGENT}\r\n"
            "\r\n"
        )

        REQUEST_SOCKET.send(data.encode())
        REQUEST_SOCKET.settimeout(self.timeout)

        # Prepare to receive HTTP response
        raw_response = bytes("".encode())

        while True:
            try:
                segment = REQUEST_SOCKET.recv(SEGMENT_BUFFER)
            except socket.timeout as error:
                Logger().message(
                    LoggerType.ERROR,
                    __file__,
                    f"Socket timed out when receiving the response buffer from ({domain}:{port})",
                )
                break

            if not segment:
                break

            raw_response += bytes(segment)

        REQUEST_SOCKET.close()

        return raw_response if raw_response != b"" else None, extension
