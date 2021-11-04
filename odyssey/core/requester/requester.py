from odyssey.core.config.config_loader import SEGMENT_BUFFER, USER_AGENT
from odyssey.core.utils.utils import SCHEMES

from urllib.parse import urlparse

import socket
import ssl
import re


def make_request(url, timeout=5):

    is_ssl = url.startswith("https")

    ssl_socket = None
    reg_socket = socket.socket()

    scheme = str(urlparse(url).scheme)
    domain = str(urlparse(url).netloc)

    scheme_port = SCHEMES.get(scheme)

    conn_port = scheme_port

    path = "/"

    if domain:
        if ":" in domain:
            domain = domain.split(":")[0]

            port_match = re.search("(http|https)://(.*)/(.*)", url)
            port_in_url = int(port_match.group(2).split(":")[1].split('/')[0])

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


        request_data = f"GET /{path} HTTP/1.1\r\nHost: {domain}\r\nAccept: */*\r\nConnection: close\r\nUser-Agent: {USER_AGENT}\r\n\r\n"


        if is_ssl:
            context = ssl.SSLContext()
            ssl_socket = context.wrap_socket(reg_socket, server_hostname=domain)
            try:
                ssl_socket.connect((domain, conn_port))
            except Exception as error:
                print(f"[ERROR] (REQUESTER) <https> Failed to resolve domain {domain}\n\n{error}")
                return

            ssl_socket.send(request_data.encode())
            ssl_socket.settimeout(timeout)


        else:

            try:
                reg_socket.connect((domain, conn_port))
            except Exception as error:
                print(f"[ERROR] (REQUESTER) <http> Failed to resolve domain {domain}\n\n{error}")
                return

            reg_socket.send(request_data.encode())
            reg_socket.settimeout(timeout)

        raw_response = bytes("".encode())

        while True:
            try:
                if is_ssl:
                    segment = ssl_socket.recv(SEGMENT_BUFFER)
                else:
                    segment = reg_socket.recv(SEGMENT_BUFFER)
            except socket.timeout:
                print("[ERROR] (REQUESTER) Socket connection timed out when receiving response segment")
                break

            if not segment:
                break

            raw_response += bytes(segment)

        if is_ssl:
            ssl_socket.close()
        else:
            reg_socket.close()

        return raw_response


