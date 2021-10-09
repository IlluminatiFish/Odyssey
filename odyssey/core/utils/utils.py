from odyssey.core.config.config_loader import CLEAR_COOKIES, DISPLAY_TRACKERS, TRACKING_COOKIES

from urllib.parse import urlparse

import requests
import socket
import ssl
import re


SCHEMES = {

    'http': 80,
    'https': 443

}


class HeaderUtils:

    def __init__(self, data):
        self.data = data

    def _parse_headers(self):

        response_headers = {}
        for delimiter in self.data:
            if delimiter:
                response_headers[delimiter.split(': ')[0].title()] = delimiter.split(': ')[1]

        return response_headers

    def get_value(self, key):
        return self._parse_headers().get(key, None)


def find_urls(data):
    pattern = re.compile('(https?:\/\/(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9])(:?\d*)\/?([a-z_\/0-9\-#.]*)\??([a-z_\/0-9\-#=&?%.]*)')
    return pattern.findall(data)


def get_cookies(raw_content):
    '''
        Gets all the cookies set by the web server given by the Set-Cookie headers in the response

        :param raw_content: The raw content taken from the do_trace(url) function.

        :returns: A list of cookies depending on the DISPLAY_TRACKERS configuration setting, could be
                  a list of tracking cookies (True) or all cookies found (False).
    '''

    headers = raw_content.split(b'\r\n\r\n', 1)[0].decode()

    header_list = headers.splitlines()

    http_headers = header_list[1:]

    cookies = []
    trackers = []

    # fold any weird cases used in the header keys while retaining the correct case for the header value
    cleaned_headers = [http_header.split(':')[0].casefold() + ':' + http_header.split(':')[1] for http_header in http_headers]

    for http_header in cleaned_headers:
        if str(http_header).startswith('set-cookie: '):
            cookie_value = str(http_header).split('set-cookie: ')[1]

            cookie_prefix = cookie_value.split('=')[0]

            if cookie_prefix in CLEAR_COOKIES:  # Skip 'good' cookies
                continue

            for tracking_cookie in TRACKING_COOKIES:
                if cookie_value.startswith(tracking_cookie):
                    trackers.append(cookie_value)

            cookies.append(cookie_value)

    if DISPLAY_TRACKERS:
        return str(trackers)
    else:
        return str(cookies)





def get_ssl_cert(url):
    '''
        Gets the ssl certificate from the :param url:

        :param url: The url you want to get the ssl certificate from.

        :returns: The ssl certificate from the :param url:
    '''

    scheme = urlparse(url).scheme
    port = 443 # Assume by default port for SSL communication is 443

    if scheme == 'http': # We don't need HTTP URLs
        return

    domain = urlparse(url).netloc

    if ':' in domain:
        domain = domain.split(':')[0]

        # Determines the SSL port that will be used in SSL communication

        port_match = re.search("(http|https)://(.*)/(.*)", url)

        port_in_url = int(port_match.group(2).split(':')[1])
        scheme_port = SCHEMES.get(scheme)

        # If the port in the url does not match the port of the scheme, then set the port from the url to be the
        # one we communicate over (eg. https://example.com:8443/path) port 8443 would be used over the port 443 set
        # by the url's scheme
        if scheme_port != port_in_url:
            port = port_in_url


    if domain:
        ip = None

        try:
            ip = socket.gethostbyname(domain) # Resolve the domain to an IP
        except Exception as error:
            print(error, 'failed to resolve on domain {}'.format(domain))

        context = ssl.SSLContext()
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_default_certs()

        base_socket = socket.socket()
        ssl_socket = context.wrap_socket(base_socket, server_hostname=domain)
        cert = None

        try:
            ssl_socket.connect((ip, port))
            cert = ssl_socket.getpeercert()
        except Exception as error:
            print(error, 'failed to connect on {}:{}'.format(ip, port))


        return cert


def get_ip_metadata(ip):
    '''
        Get relevant data/information about a specific IP address.

        :param ip: The IP address you want to get data on.

        :returns: The JSON response of the API
    '''

    request = requests.get('http://ip-api.com/json/{}'.format(ip))
    return request.json()
