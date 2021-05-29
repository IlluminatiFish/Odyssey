from odyssey.core.config.config_loader import USER_AGENT
from odyssey.core.parser.content_parser import process_response
from odyssey.core.requestor.http_request import http_response
from odyssey.core.requestor.https_request import https_response
from odyssey.core.utils.get_cookies import get_cookies
from odyssey.core.utils.get_server import get_server

import socket
from urllib.parse import urlparse

trace = {}  # Trace URL redirect path


def do_trace(param_url):
    '''
        Recursively finds the next URL in the redirect chain and adds it to the trace path

        :param param_url: The url that is being traced for redirects

        :returns: A dictionary representation of the path the redirects took
    '''

    request_socket = socket.socket()  # Request TCP Socket

    scheme = str(urlparse(param_url).scheme)
    domain = str(urlparse(param_url).netloc)

    root_url = scheme + '://' + domain

    path = '/'

    if domain:

        if ':' in domain:
            domain = domain.split(':')[0]

        raw_path = param_url.split('://')[1].split('/', 1)[1] if len(param_url.split('://')[1].split('/')) > 1 else ""

        path = raw_path  # Set current path to the raw_path

        if urlparse(raw_path).query:

            path = urlparse(raw_path).path + '?' + urlparse(raw_path).query

            if urlparse(raw_path).fragment:
                path = path + '#' + urlparse(raw_path).fragment

        if urlparse(
                raw_path).fragment:  # If we have a fragement in the URL such as (https://bit.ly/37O7zEf#HJEDY_BRMFE_6PIHS) we should get rid of it
            path = path.split('#')[0]

    request_message = f"GET /{path} HTTP/1.1\r\nHost: {domain}\r\nAccept: */*\r\nConnection: close\r\nUser-Agent: {USER_AGENT}\r\n\r\n"

    response = None

    if scheme == "http":
        port = 80
        response = http_response(request_socket, domain, port, request_message)

    if scheme == "https":
        port = 443
        response = https_response(request_socket, domain, port, request_message)

    if response:

        # Parse the response accordingly here

        next_url = process_response(response, param_url)

        trace[param_url] = socket.gethostbyname(domain) + '**' + get_server(response) + '**' + get_cookies(response,
                                                                                                           True)
        if next_url is not None:
            if param_url != next_url:  # Fixes endless redirect loops that are on the same URL
                if next_url not in trace.keys():
                    if next_url.startswith('/'):  # Local page based redirects
                        do_trace(root_url + next_url)

                    do_trace(next_url)

            else:
                return

    request_socket.close()
    return trace
