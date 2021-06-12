from odyssey.core.config.config_loader import USER_AGENT
from odyssey.core.parser.content_parser import process_response
from odyssey.core.requestor.http_request import http_response
from odyssey.core.requestor.https_request import https_response
from odyssey.core.utils.get_cookies import get_cookies
from odyssey.core.utils.get_server import get_server

import socket, re
from urllib.parse import urlparse

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

    request_socket = socket.socket()  # Request TCP Socket

    scheme = str(urlparse(param_url).scheme)
    domain = str(urlparse(param_url).netloc)

    root_url = scheme + '://' + domain

    # Set the port we will use in the socket for the request, to the equivalent port of the url scheme initially
    port = schemes.get(scheme)

    path = '/'

    if domain:

        # If a colon is found in the raw domain meaning it has a port
        if ':' in domain:
            domain = domain.split(':')[0]

            # Find any port that may exist in the url
            port_match = re.search('(http|https)://(.*)/(.*)', param_url)

            port_in_url = int(port_match.group(2).split(':')[1])
            scheme_port = schemes.get(scheme)

            # If the port in the url does not match the port of the scheme, then set the port from the url to be the
            # one we communicate over (eg. http://example.com:8888/path) port 8888 would be used over the port 80 set
            # by the url's scheme
            if scheme_port != port_in_url:
                port = port_in_url

            # Removed any ports found in the raw domain of a url
            param_url = param_url.replace(port_match.group(2), domain)

        raw_path = param_url.split('://')[1].split('/', 1)[1] if len(param_url.split('://')[1].split('/')) > 1 else ""

        path = raw_path  # Set current path to the raw_path

        if urlparse(raw_path).query:

            path = urlparse(raw_path).path + '?' + urlparse(raw_path).query

            if urlparse(raw_path).fragment:
                path = path + '#' + urlparse(raw_path).fragment

        if urlparse(
                raw_path).fragment:  # If we have a fragement in the URL such as (https://bit.ly/37O7zEf#HJEDY_BRMFE_6PIHS) we should get rid of it
            path = path.split('#')[0]

    request_message = "GET /{} HTTP/1.1\r\nHost: {}\r\nAccept: */*\r\nConnection: close\r\nUser-Agent: {}\r\n\r\n".format(
        path, domain, USER_AGENT)

    response = None

    if scheme == "http":
        response = http_response(request_socket, domain, port, request_message)

    if scheme == "https":
        response = https_response(request_socket, domain, port, request_message)

    if response:

        trace[param_url] = socket.gethostbyname(domain) + '**' + get_server(response) + '**' + get_cookies(response,
                                                                                                           True)

        # Parse the response accordingly here
        next_url = process_response(response, param_url)

        if next_url:
            if param_url != next_url:  # Fixes endless redirect loops that are on the same URL
                if next_url not in trace.keys():
                    if next_url.startswith('/'):  # Local page based redirects
                        do_trace(root_url + next_url)

                    do_trace(next_url)

            else:
                return

    request_socket.close()
    return trace
