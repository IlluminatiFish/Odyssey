from odyssey.core.parser.response_parser import ResponseParser
from odyssey.core.requester.requester import make_request
from odyssey.core.utils.utils import HeaderUtils, get_cookies

from urllib.parse import urlparse

import socket


trace = {}  # Trace URL redirect path


def do_trace(param_url):
    '''
        Recursively finds the next URL in the redirect chain and adds it to the trace path

        :param param_url: The url that is being traced for redirects

        :returns: A dictionary representation of the path the redirects took
    '''


    scheme = str(urlparse(param_url).scheme)
    host = str(urlparse(param_url).netloc)

    # Get rid of the port from the host part of the URL
    if ':' in host:
        host = host.split(':')[0]

    root_url = scheme + '://' + host

    raw_response = make_request(param_url)

    if not raw_response:
        print(f'[-] No response was received from {param_url}')
        return

    raw_headers = raw_response.split(b'\r\n\r\n', 1)[0].decode()

    header_list = raw_headers.splitlines()

    response_headers = header_list[1:]

    if raw_response:

        header_utils = HeaderUtils(response_headers)

        ip = None

        try:
            ip = socket.gethostbyname(host)
        except socket.error as error:
            print(f'[-] Could not resolve {host} to an IP, while tracing {param_url}')
            return

        trace[param_url] = (ip, header_utils.get_value('Server'), get_cookies(raw_response))

        # Parse the response accordingly here
        parser = ResponseParser(raw_response, param_url)
        next_url = parser.parse()

        if not next_url:
            return

        if param_url != next_url and next_url not in trace.keys():
            if next_url.startswith('/'):  # Fixes endless redirect loops that are on the same URL and checks if its a local based page redirect
                do_trace(root_url + next_url)
            else:
                do_trace(next_url)
        else:
            return


    return trace
