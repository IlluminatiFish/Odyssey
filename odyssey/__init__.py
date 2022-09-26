from typing import Any, Dict, List, Tuple, Union

from bs4 import BeautifulSoup
from furl import furl

from odyssey.body.handlers import BodyHandlers
from odyssey.header.handlers import HeaderHandlers
from odyssey.request import Request
from odyssey.response import Response
from odyssey.utils import get_ip_from_url, parse_cookies


class Odyssey:
    """Main class that the user can interact with."""

    def __init__(self) -> None:

        # Dictionary of visited URLs & their respective metadata
        self._visited_urls: Dict[str, Dict[str, Any]] = {}

    def check(
        self, url: str, timeout: int = 5
    ) -> Union[Dict[str, Dict[str, Any]], None]:
        """
        Find all the URLs in the traceroute.

        Args:
            url (str):
                A Uniform Resource Locator (URL).
            timeout (int):
                The amount of seconds a socket should timeout after.

        Returns:
            If None is returned, no redirects were identified.

            Otherwise, a dictionary of URLs with their associated
            metadata should be returned.
        """

        # Holds metadata for a given URL
        metadata = {}

        # Next URI in the chain & the associated metadata
        redirect_uri, uri_server, uri_cookies = self._find_redirect(url, timeout)

        # Obtain the IP address of the domain from the URL
        ip = get_ip_from_url(url)

        if ip:
            metadata.update({"ip": ip})

        if uri_server:
            metadata.update({"server": uri_server})

        # Check if any cookies are present
        if uri_cookies:
            metadata.update({"cookies": parse_cookies(uri_cookies)})

        # Append URL with its metadata to visited URLs dictionary
        self._visited_urls[url] = metadata

        # A URL cannot redirect to itself
        if url == redirect_uri:
            return

        # Is the redirect valid
        if redirect_uri is None:
            return

        # Have we already visited this URL
        if redirect_uri in list(self._visited_urls.keys()):
            return

        # Local redirect to another path on the same web server
        if redirect_uri.startswith("/"):

            # Identify the last root URL in the redirect chain
            root_urls = [
                f"{furl(url).scheme}://{furl(url).host}"
                for url in list(self._visited_urls.keys())[::-1]
            ]

            last_root_url = root_urls[0]

            redirect_uri = last_root_url + redirect_uri

        # Scan the next URL in the chain
        self.check(redirect_uri, timeout)

        # Return visited URLs dict
        return self._visited_urls

    def _find_redirect(
        self, url: str, timeout: int
    ) -> Tuple[Union[str, None], Union[str, None], Union[List[str], None]]:
        """
        Identifies the redirect URL, by first checking the response headers,
        then checking the response body.

        Args:
            url (str):
                A Uniform Resource Locator (URL).
            timeout (int):
                The amount of seconds a socket should timeout after.

        Returns:
            Could return a populated tuple or a tuple of None values.

            If no response was received from the request, a tuple of None values
            is returned.

            Otherwise, a tuple should be returned with the next redirect URI in the chain,
            along with its server header and cookies it sets in the response.
        """

        request = Request(url, timeout)

        raw_response = request.execute()

        # If no response was received from the request
        if not raw_response:
            return None, None, None

        parsed_headers, parsed_body = Response(raw_response).parse()

        # Attempt to find redirects from header first then attempt to find redirects inside the response body
        redirect_uri = None

        if not redirect_uri:
            redirect_uri = self._find_header_redirect(parsed_headers.dump())

        # If the redirect_uri is still not found
        if not redirect_uri:

            content_type = parsed_headers.get("Content-Type")

            raw_content_type_metadata = content_type.split(";")[1:]
            content_type_metadata = [
                metadata_element.strip()
                for metadata_element in raw_content_type_metadata
            ]

            metadata_dictionary = {}

            for metadata_element in content_type_metadata:
                parameter, value = metadata_element.split("=")
                metadata_dictionary[parameter] = value

            # Uses the charset supplied in the Content-Type header if no charset is
            # identified, it defaults the charset to cp437.
            content_charset = metadata_dictionary.get("charset", "cp437")

            response_body = parsed_body.decode(content_charset)

            # Only parse response bodies that start and end with the magic html tags
            if response_body.startswith("<html>") and response_body.endswith("</html>"):
                redirect_uri = self._find_body_redirect(response_body)

        return (
            redirect_uri,
            parsed_headers.get("Server"),
            parsed_headers.get("Set-Cookie"),
        )

    @staticmethod
    def _find_header_redirect(headers: Dict[str, List[str]]) -> Union[str, None]:
        """
        Identifies redirects in a given request's Location & Refresh headers.

        Args:
            headers (Dict[str, List[str]):
                A dictionary mapping header keys to the corresponding header values

        Returns:
            Could return a string or None. If None is returned, no redirect URI was identified.
            Otherwise, a string should be returned which is pointed to the next URI in the redirect chain.
        """

        redirect_uri = None

        location_headers = headers.get("Location", None)
        refresh_headers = headers.get("Refresh", None)

        if isinstance(location_headers, list):
            redirect_uri = HeaderHandlers().handle_location_headers(
                headers=location_headers
            )

        if isinstance(refresh_headers, list):
            redirect_uri = HeaderHandlers().handle_refresh_headers(
                headers=refresh_headers
            )

        return redirect_uri

    @staticmethod
    def _find_body_redirect(body: str) -> Union[str, None]:
        """
        Identifies redirects in a given response body.

        Args:
            body (str):
                A string representation of the response body.

        Returns:
            Could return a string or None. If None is returned, no redirect URI was identified.
            Otherwise, a string should be returned which is pointed to the next URI in the redirect chain.
        """

        redirect_uri = None

        soup = BeautifulSoup(body, "html.parser")

        meta_tags = soup.find_all("meta")

        if len(meta_tags) > 0:
            redirect_uri = BodyHandlers().handle_meta_tags(tags=meta_tags)

        return redirect_uri
