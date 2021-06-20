from odyssey.core.config.config_loader import SEGMENT_BUFFER, USER_AGENT

from urllib.parse import urlparse

import socket, ssl, re

schemes = {

    'http': 80,
    'https': 443

}


def make_request(url, timeout=5):

    is_ssl = url.startswith("https")

    ssl_socket = None
    reg_socket = socket.socket()

    scheme = str(urlparse(url).scheme)
    domain = str(urlparse(url).netloc)

    scheme_port = schemes.get(scheme)

    conn_port = scheme_port

    path = "/"

    if domain:
        if ":" in domain:
            domain = domain.split(":")[0]

            port_match = re.search("(http|https)://(.*)/(.*)", url)
            port_in_url = int(port_match.group(2).split(":")[1])

            if scheme_port != port_in_url:
                conn_port = port_in_url

            url = url.replace(port_match.group(2), domain)

        raw_path = url.split("://")[1].split("/", 1)[1] if len(url.split("://")[1].split("/")) > 1 else ""
        path = raw_path

        if urlparse(raw_path).query:
            path = urlparse(raw_path).path + "?" + urlparse(raw_path).query

            if urlparse(raw_path).fragment:
                path = path + '#' + urlparse(raw_path).fragment

        if urlparse(
                raw_path).fragment:  # If we have a fragement in the URL such as (https://bit.ly/37O7zEf#HJEDY_BRMFE_6PIHS) we should get rid of it
            path = path.split('#')[0]


        request_message = f"GET /{path} HTTP/1.1\r\nHost: {domain}\r\nAccept: */*\r\nConnection: close\r\nUser-Agent: {USER_AGENT}\r\n\r\n"


        if is_ssl:
            context = ssl.SSLContext()
            ssl_socket = context.wrap_socket(reg_socket, server_hostname=domain)
            try:
                ssl_socket.connect((domain, conn_port))
            except socket.gaierror:
                print(f"[HTTPS] Failed to resolve domain {domain}")
                return

            ssl_socket.send(request_message.encode())
            ssl_socket.settimeout(timeout)


        else:

            try:
                reg_socket.connect((domain, conn_port))
            except socket.gaierror:
                print(f"[HTTP] Failed to resolve domain {domain}")
                return

            reg_socket.send(request_message.encode())
            reg_socket.settimeout(timeout)

        raw_response = bytes("".encode())

        while True:
            try:
                if is_ssl:
                    segment = ssl_socket.recv(SEGMENT_BUFFER)
                else:
                    segment = reg_socket.recv(SEGMENT_BUFFER)
            except socket.timeout:
                print("[REQUESTOR] Socket connection timed out when receiving response segment")
                break

            if not segment:
                break

            raw_response += bytes(segment)

        if is_ssl:
            ssl_socket.close()
        else:
            reg_socket.close()

        return raw_response


