import requests


def getData(ip, type):
    '''
        @:purpose: Get relevant data/information about a specific IP address.

        @:param ip: The IP address you want to get data on.
        @:param type: The type of data you want about the IP.
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

        @:returns request.json[type]: The type of data about the IP you requested.
    '''

    request = requests.get('http://ip-api.com/json/{}'.format(ip))
    if len(request.json()[type]) > 0:
        return request.json()[type]
    else:
        return None

def dictionarize(request_data):
    '''
        @:purpose: Convert the HTTP response of a web server to a dictionary
                   for ease of use.

        @:param request_data: The response data from the web server.

        @:returns request_headers: The request headers as a dictionary
    '''

    request_headers = {}
    for splitter in request_data:
        # Quick patch, that checks if the header entry exists
        if splitter:
            # Quick patch, with title() to capitalize all header entries
            request_headers[splitter.split(': ')[0].title()] = splitter.split(': ')[1]

    return request_headers


def getValue(key, request_data):
    '''
        @:purpose: Get a header key from the dictionarized request response list.

        @:param key: The key you want to get the data from in the headers.
        @:param request_data: The response data from the web server.

        @:returns dictionarize(request_data)[key]: The value in the header @:param key
    '''

    try:
        return dictionarize(request_data)[key]
    except KeyError:
        return
