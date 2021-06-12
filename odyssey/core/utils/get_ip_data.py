import requests


def get_ip_data(ip):
    '''
        Get relevant data/information about a specific IP address.

        :param ip: The IP address you want to get data on.

        :returns: The JSON response of the API
    '''

    request = requests.get('http://ip-api.com/json/{}'.format(ip))
    return request.json()
