from odyssey.core.config.config_loader import CLEAR_COOKIES, TRACKING_COOKIES


def get_cookies(raw_content, tracking):
    '''
        Gets all the cookies set by the web server given by the Set-Cookie headers in the response

        :param raw_content: The raw content taken from the do_get(url) function.
        :param tracking: A setting if you want only tracking cookies or all cookies from this function.

        :returns: A list of cookies depending on the :param tracking: setting, could be
                  a list of tracking cookies or all cookies found.
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

    if tracking:
        return str(trackers)
    else:
        return str(cookies)
