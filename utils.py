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

    content = raw_content.decode()

    headers = content.split('\r\n\r\n', 1)[0]
    header_list = headers.splitlines()
    http_headers = header_list[1:]

    return str(get_value('Server', http_headers))
