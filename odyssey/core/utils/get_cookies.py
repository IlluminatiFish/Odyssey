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

    clear_cookie_prefixes = ['__CFDUID', '_BIT', 'PHPSESSID', 'XSRF-TOKEN']

    tracking_cookie_prefixes = [
        'ENC_AFF_SESSION_',
        'HO_MOB',
        'CEP-V4',
        'UNIQUECLICK_',
        'CLICK_ID',
        'VOLUUM-CID-V4',
        'TRACKINGID',
        'LT_TR',
        'CLICKS',
        'BRWSR',
        'HEXA.SID',  # hexa.sid
        'TRK',
        'TRACKINGID',
        'GEOIP_COUNTRY',
        'LANGUAGECODE',
        'CC-V4',
        'UCLICK',
        'LNG',
        'FLAGLNG'
    ]

    cookies = []
    trackers = []

    for http_header in http_headers:
        if str(http_header.upper()).startswith('SET-COOKIE: '):

            cookie_value = str(http_header.upper()).split('SET-COOKIE: ')[1]

            cookie_prefix = cookie_value.split('=')[0]

            if cookie_prefix in clear_cookie_prefixes:  # Skip 'good' cookies
                continue

            for tracking_cookie_prefix in tracking_cookie_prefixes:
                if cookie_value.startswith(tracking_cookie_prefix):
                    print('[!] Tracking cookie detected\n\t- Cookie Value: {}'.format(cookie_value))
                    trackers.append(cookie_value)

            cookies.append(cookie_value)

    if tracking:
        return str(trackers)
    else:
        return str(cookies)
