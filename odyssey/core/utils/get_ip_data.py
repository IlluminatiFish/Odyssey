import requests


def get_ip_data(ip):
    '''
        Get relevant data/information about a specific IP address.

        :param ip: The IP address you want to get data on.

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
    return request.json()