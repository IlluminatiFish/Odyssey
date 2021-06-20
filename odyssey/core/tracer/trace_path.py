from odyssey.core.parser.content_parser import process_response
from odyssey.core.requestor.requestor import make_request
from odyssey.core.utils.get_cookies import get_cookies
from odyssey.core.utils.get_server import get_server

from urllib.parse import urlparse

import socket

trace = {}  # Trace URL redirect path


schemes = {

    'http': 80,
    'https': 443

}


def do_trace(param_url):
    '''
        Recursively finds the next URL in the redirect chain and adds it to the trace path

        :param param_url: The url that is being traced for redirects

        :returns: A dictionary representation of the path the redirects took
    '''

    scheme = str(urlparse(param_url).scheme)
    domain = str(urlparse(param_url).netloc)

    root_url = scheme + '://' + domain

    raw_response = make_request(param_url)

    if raw_response:

        trace[param_url] = socket.gethostbyname(domain) + '**' + get_server(raw_response) + '**' + get_cookies(raw_response,
                                                                                                           True)

        # Parse the response accordingly here
        next_url = process_response(raw_response, param_url)

        if next_url:
            if param_url != next_url:  # Fixes endless redirect loops that are on the same URL
                if next_url not in trace.keys():
                    if next_url.startswith('/'):  # Local page based redirects
                        do_trace(root_url + next_url)

                    do_trace(next_url)

            else:
                return

    return trace
