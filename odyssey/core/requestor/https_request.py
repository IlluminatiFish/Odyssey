import socket, ssl

from odyssey.core.utils.constants import SEGMENT_BUFFER


def https_response(param_socket, domain, port, request, timeout=5):
    '''
        Makes a HTTPS request to the specific domain & port using python sockets

        :param param_socket: The socket object that the request is being performed on
        :param domain: The domain you are contacting via the HTTPS request
        :param port: The port you are using in the HTTPS request
        :param request: The HTTP request sent to the server
        :param timeout: The time until the server does not respond with data

        :returns: The raw bytes respond from the web server
    '''

    context = ssl.SSLContext()
    ssl_socket = context.wrap_socket(param_socket, server_hostname=domain)
    try:
        ssl_socket.connect((domain, port))
    except socket.gaierror as error:
        print(f"[HTTPS] Failed to resolve domain {domain}")
        return

    ssl_socket.send(request.encode())
    ssl_socket.settimeout(timeout)

    raw_response = bytes("".encode())

    while True:
        try:
            segment = ssl_socket.recv(SEGMENT_BUFFER)
        except socket.timeout as error:
            print("[HTTPS] Socket connection timed out when receiving response buffer")
            break

        if not segment:
            break

        raw_response += bytes(segment)

    return raw_response
