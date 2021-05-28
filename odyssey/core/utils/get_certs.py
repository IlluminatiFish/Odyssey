import socket
import ssl
from urllib.parse import urlparse


def get_ssl_cert(url):
    '''
        Gets the ssl certificate from the :param url:

        :param url: The url you want to get the ssl certificate from.

        :returns: The ssl certificate from the :param url:
    '''

    scheme = urlparse(url).scheme

    if scheme == 'http': # We don't need HTTP URLs
        return

    domain = urlparse(url).netloc
    if ':' in domain:
        domain = domain.split(':')[0]

    if domain:
        ip = None

        try:
            ip = socket.gethostbyname(domain) # Resolve the domain to an IP
        except Exception as exec:
            print(exec, 'failed to resolve on domain {}'.format(domain))

        context = ssl.SSLContext()
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_default_certs()

        base_socket = socket.socket()
        ssl_socket = context.wrap_socket(base_socket, server_hostname=domain)
        cert = None

        try:
            ssl_socket.connect((ip, 443))
            cert = ssl_socket.getpeercert()
        except Exception as exec:
            print(exec, 'failed to connect on {}:{}'.format(ip, 443))

        return cert


