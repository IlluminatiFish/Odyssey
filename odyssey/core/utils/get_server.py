from odyssey.core.utils.odyssey_utils import get_value


def get_server(raw_content):
    '''
        Gets the Server header from the web server's response

        :param raw_content: The raw content taken from the do_get(url) function.

        :returns: The type of the web server (ex. Apache, Nginx, etc.)
    '''

    headers = raw_content.split(b'\r\n\r\n', 1)[0].decode()

    header_list = headers.splitlines()

    http_headers = header_list[1:]

    return str(get_value('Server', http_headers))
