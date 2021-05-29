from odyssey.core.config.config_loader import SEGMENT_BUFFER

import socket


def http_response(param_socket, domain, port, request, timeout=5):
    '''
        Makes a HTTP request to the specific domain & port using python sockets

        :param param_socket: The socket object that the request is being performed on
        :param domain: The domain you are contacting via the HTTP request
        :param port: The port you are using in the HTTP request
        :param request: The HTTP request sent to the server
        :param timeout: The time until the server does not respond with data

        :returns: The raw bytes respond from the web server
    '''

    try:
        param_socket.connect((domain, port))
    except socket.gaierror as error:
        print(f"[HTTP] Failed to resolve domain {domain}")
        return

    param_socket.send(request.encode())
    param_socket.settimeout(timeout)

    raw_response = bytes("".encode())

    while True:
        try:
            segment = param_socket.recv(SEGMENT_BUFFER)
        except socket.timeout:
            print("[HTTP] Socket connection timed out when receiving response buffer")
            break

        if not segment:
            break

        raw_response += bytes(segment)

    return raw_response
