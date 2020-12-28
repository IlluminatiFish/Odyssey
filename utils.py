import re, requests


def get_data(ip, type):
    '''
        Get relevant data/information about a specific IP address.

        :param ip: The IP address you want to get data on.
        :param type: The type of data you want about the IP.

            Possibilities:
                - country
                - countryCode
                - region
                - regionName
                - city
                - zip
                - lat
                - lon
                - timezone
                - as
                - isp
                - org

        :returns: The type of data about the IP you requested.
    '''

    request = requests.get('http://ip-api.com/json/{}'.format(ip))
    if len(request.json()[type]) > 0:
        return request.json()[type]
    else:
        return None

def dictionarize(request_data):
    '''
        Convert the HTTP response of a web server to a dictionary for ease of use.

        :param request_data: The response data from the web server.

        :returns: The request headers as a dictionary
    '''

    request_headers = {}
    for splitter in request_data:
        # Quick patch, that checks if the header entry exists
        if splitter:
            # Quick patch with title() to capitalize all header entries
            request_headers[splitter.split(': ')[0].title()] = splitter.split(': ')[1]

    return request_headers


def get_value(key, request_data):
    '''
        Get a header key from the dictionarized request response list.

        :param key: The key you want to get the data from in the headers.
        :param request_data: The response data from the web server.

        :returns: The value in the header :param key:
    '''

    try:
        return dictionarize(request_data)[key]
    except KeyError:
        return None

def find_urls(data):
    '''
        Gets all the strings that match the regex pattern for URLs.

        :param data: The string/data you want to check to see if URLs exist in them.

        :returns: The list of strings that match the regex pattern in :param data:
    '''

    regex = re.compile('http[s]?://(?:[\w]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.UNICODE)
    return regex.findall(data)



def get_server(raw_content):
    '''
        Gets the Server header from the web server's response

        :param raw_content: The raw content taken from the do_get(url) function.

        :returns: The type of the web server (ex. Apache, Nginx, etc.)
    '''

    # Very bad method, as it does not account for all other language characters, needs to be fixed in the future
    content = raw_content.decode()

    headers = content.split('\r\n\r\n', 1)[0]
    header_list = headers.splitlines()
    http_headers = header_list[1:]

    return str(get_value('Server', http_headers))


def get_cookies(raw_content, tracking):
    '''
        Gets all the cookies set by the web server given by the Set-Cookie headers in the response

        :param raw_content: The raw content taken from the do_get(url) function.
        :param tracking: A setting if you want only tracking cookies or all cookies from this function.

        :returns: A list of cookies depending on the :param tracking: setting, could be
                  a list of tracking cookies or all cookies found.
    '''

    # Very bad method, as it does not account for all other language characters, needs to be fixed in the future
    content = raw_content.decode()

    headers = content.split('\r\n\r\n', 1)[0]
    header_list = headers.splitlines()
    http_headers = header_list[1:]

    # Tracking cookies identified

    # Prefix: - Usage
    # enc_aff_session_* and ho_mob: - https://help.tune.com/hasoffers/pixel-tracking/ / https://gyazo.com/09cd1743faefd10104850b995b982591
    # cep-v4: - https://webcookies.org/cookie/http/cep-v4/1407350
    # voluum-cid-v4: - https://voluum.com/
    # trackingID: -  N/A

    clear_cookie_prefixes = ['__cfduid', '_bit', 'PHPSESSID', 'XSRF-TOKEN'] # Skips 'good' cookies
    tracking_cookie_prefixes = ['enc_aff_session_', 'ho_mob', 'cep-v4', 'uniqueClick_', 'click_id', 'voluum-cid-v4', 'trackingID']

    cookies = []
    trackers = []


    for http_header in http_headers:
        if str(http_header).startswith('Set-Cookie: '):

            cookie_value = str(http_header).split('Set-Cookie: ')[1]
            cookie_prefix = cookie_value.split('=')[0]

            if cookie_prefix in clear_cookie_prefixes: # Skip 'good' cookies
                continue


            for tracking_cookie_prefix in tracking_cookie_prefixes:
                if cookie_value.startswith(tracking_cookie_prefix):
                    print('[!] Tracking cookie detected\n\t- Cookie Value: {}'.format(cookie_value))
                    trackers.append(cookie_value)

            cookies.append(cookie_value)

    if tracking == True:
        return str(trackers)
    else:
        return str(cookies)
