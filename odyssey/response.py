from typing import Tuple

from odyssey.utils import Headers


class Response:
    def __init__(self, raw_response: bytes) -> None:
        """
        Response class constructor.

        Args:
            raw_response (bytes):
                A string of bytes containing the response body.
        """
        self.raw_response = raw_response

    def parse(self) -> Tuple[Headers, bytes]:
        """
        Parses the HTTP response.

        Returns:
            A tuple consisting of the parsed response headers & body.
        """

        raw_headers = self.raw_response.split(b"\r\n\r\n", 1)[0].decode()

        raw_body = self.raw_response.split(b"\r\n\r\n", 1)[1]

        header_list = raw_headers.splitlines()

        response_headers = Headers(header_list[1:])

        return response_headers, raw_body
