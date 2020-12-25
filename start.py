import socket, ssl
from urllib.parse import urlparse

from contentparser import processContent
from utils import getData

VISITED = {}
SEGMENT_BUFFER = 8192 # How big you want each sock.recv() call to take byte-wise
TIMEOUT = 10
ua = "Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0"

def doGET(url):
    '''
        @:purpose: Sends a correctly formed HTTP 'GET' request using sockets,
                   to get content from the web server.

        @:param url: The URL where you want to get the content from.

        @:returns raw_response: Returns the raw bytes response from the web server.
    '''

    if url is not None:
        scheme = str(urlparse(url).scheme)
        domain = str(urlparse(url).netloc)

        if domain:
            if ':' in domain: # Catches ports in the netloc from urlparse (Ex. some.domain:xxxx)
                domain = domain.split(':')[0]

            raw_path = url.split('://')[1].split('/', 1)[1] if len(url.split('://')[1].split('/')) > 1 else ""

            path = raw_path # Set current path to the raw_path

            # This gets rid of any fragements or queries in the URL
            if urlparse(raw_path).query:
                path = urlparse(raw_path).path + '?' + urlparse(raw_path).query

            if urlparse(raw_path).fragment:
                path = urlparse(raw_path).path

            port = 80 if scheme == "http" else 443

            sock = socket.socket()

            request = "GET /{} HTTP/1.1\r\nHost: {}\r\nAccept: */*\r\nConnection: close\r\nUser-Agent: {}\r\n\r\n".format(
                path, domain, ua)

            if scheme == 'http':
                sock.connect((domain, port))
                sock.send(request.encode())
                sock.settimeout(TIMEOUT)  # Default socket operation timeout of X seconds

                raw_response = bytes("".encode())
                while True:
                    try:
                        segment = sock.recv(SEGMENT_BUFFER)
                    except socket.timeout as exc:
                        print('[-] Socket receiver timed out after {} seconds'.format(TIMEOUT))
                        break
                    if not segment:
                        break
                    raw_response += bytes(segment)

                VISITED[url] = socket.gethostbyname(domain)
                next_url = processContent(raw_response, url)
                '''
                    If the current url & next url are the same then do not accept
                '''
                if url != next_url:
                    '''
                        Fixes the script going into an endless loop of the same redirects
                    '''
                    if next_url not in VISITED.keys():
                        doGET(next_url)
                    else:
                        return

                sock.close()

            if scheme == 'https':
                context = ssl.SSLContext()
                ssl_sock = context.wrap_socket(sock, server_hostname=domain)
                try:
                    ssl_sock.connect((domain, port))
                except socket.gaierror as ex:
                    print('[-] Failed to resolve domain ({})'.format(domain))
                    return

                ssl_sock.send(request.encode())
                ssl_sock.settimeout(TIMEOUT) # Default socket operation timeout of X seconds

                raw_response = bytes("".encode())
                while True:
                    try:
                        segment = ssl_sock.recv(SEGMENT_BUFFER)
                    except socket.timeout as ex:
                        print('[-] Socket receiver timed out after {} seconds'.format(TIMEOUT))
                        break

                    if not segment:
                        break
                    raw_response += bytes(segment)

                VISITED[url] = socket.gethostbyname(domain)
                next_url = processContent(raw_response, url)
                '''
                    If the current url & next url are the same then do not accept
                '''
                if url != next_url:

                    '''
                        Fixes the script going into an endless loop of the same redirects
                    '''
                    if next_url not in VISITED.keys():
                        doGET(next_url)
                    else:
                        return

                ssl_sock.close()

URL = input('[*] URL: ')
doGET(URL)

if len(VISITED.keys()) > 0:
    print()
    print('[+] Redirect Traceroute (Size: {})'.format(len(VISITED.keys())))
    print()
    count = 1
    for url, msg in VISITED.items():
        if url:
            print('[No. {}] [{}] ({}, {}, {})  {}'.format(x, getData(msg, 'country'), msg, getData(msg, 'as'), getData(msg, 'org'), url))
            count += 1
