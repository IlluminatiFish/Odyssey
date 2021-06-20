from urllib.parse import urlparse

import socket, ssl, re


schemes = {

    'http': 80,
    'https': 443

}

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
        scheme_port = schemes.get(scheme)

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


