import re


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

