import folium

from furl import furl

from odyssey import Odyssey
from odyssey.utils import (get_ip_address_information, get_ssl_cert_from_url,
                           match_ip_logger)


def main():

    url = input('[+] URL: ')

    traceroute = Odyssey().check(url)

    if traceroute == {} or not traceroute:
        print('[-] No redirects were identified')
        return

    MAP_CENTER = [0, 0]
    route_map = folium.Map(location=MAP_CENTER, zoom_start=2.5)
    TRACEROUTE_MAP_FILENAME = 'route.html'
    locations = []

    for hop_count, (url, metadata) in enumerate(traceroute.items(), start = 1):

        server = metadata.get('server')
        cookies = metadata.get('cookies')
        ip = metadata.get('ip')

        parsed_url = furl(url)
        domain = parsed_url.host

        country, isp, org, asn, latitude, longitude = get_ip_address_information(ip)

        result = f"[No. {hop_count}]\n\t - Server: {server}\n\t - Country: {country} \n\t - Metadata: {ip} ({isp}, {org}, {asn})\n\t - URL: {url}"

        if cookies:

            cookie_count = len(cookies)

            if cookie_count > 0:
                result += f'\n\t ' \
                          f'- Cookies:\n\t\t ' \
                          f'- Count: {cookie_count}\n\t\t ' \
                          f'- Cookie Values:'

                for cookie_name, cookie_data in cookies.items():

                    cookie_value = cookie_data.get('value')
                    cookie_attributes = cookie_data.get('attributes')

                    result += f'\n\t\t\t - Name: {cookie_name}'
                    result += f'\n\t\t\t\t - Value: {cookie_value}'
                    result += f'\n\t\t\t\t - Attributes: {cookie_attributes}'

        IS_HTTPS = parsed_url.scheme == 'https'
        
        if IS_HTTPS:

            certificate = get_ssl_cert_from_url(url)

            subject_common_name = certificate.get('subject').get('commonName')
            issuer_organization = certificate.get('issuer').get('organizationName')
            serial_number = certificate.get('serialNumber')

            result += f'\n\t ' \
                      f'- SSL Certificate:\n\t\t ' \
                      f'- Subject: {subject_common_name}\n\t\t ' \
                      f'- Issuer: {issuer_organization}\n\t\t ' \
                      f'- Serial Number: {serial_number} '

            matched_ip_logger = match_ip_logger(domain, ip, subject_common_name, serial_number, is_https = IS_HTTPS)
        else:
            matched_ip_logger = match_ip_logger(domain, ip, None, None, is_https = IS_HTTPS)

        if matched_ip_logger:
            result += '\n\t - IP Loggers:'
            result += '\n\t\t\t - ' + matched_ip_logger

        result += '\n'
        print(result)

        # Route map generation using Folium
        html = f'''
                   <link rel="preconnect" href="https://fonts.gstatic.com">
                   <link href="https://fonts.googleapis.com/css2?family=Space+Mono&display=swap" rel="stylesheet">
                   <p style="font-family: 'Space Mono', monospace;">
                       URL: {url}
                       <br>
                       IP: {ip}
                       <br>
                       ASN: {asn.split(' ')[0]}
                       <br>
                       ORG: {org}
                       <br>
                       ISP: {isp}
                   </p>
               '''

        iframe = folium.IFrame(html, width = 600, height = 250)
        popup = folium.Popup(iframe)

        # Added to avoid confusion, to see if URL coords are already in list,
        # if so adjust the next URL's coords to be distinct from the previous URL.
        offset = 0.005

        if (latitude, longitude) in locations:
            latitude, longitude = latitude + offset, longitude + offset

        # Setting up the markers for the FoliumJS map
        START_DATA = (1, 'green')
        BOUNCE_DATA = ([x for x in range(1, len(traceroute))], 'orange')
        END_DATA = (len(traceroute), 'red')

        if hop_count == START_DATA[0]:

            folium.Marker((latitude, longitude), popup = popup,
                          icon = folium.Icon(color = START_DATA[1], icon = "glyphicon-flash",
                                             prefix = "glyphicon")).add_to(
                route_map)

        elif hop_count == END_DATA[0]:

            folium.Marker((latitude, longitude), popup = popup,
                          icon = folium.Icon(color = END_DATA[1], icon = "glyphicon-flash",
                                             prefix = "glyphicon")).add_to(
                route_map)
        else:

            folium.Marker((latitude, longitude), popup = popup,
                          icon = folium.Icon(color = BOUNCE_DATA[1], icon = "glyphicon-flash",
                                             prefix = "glyphicon")).add_to(route_map)

        locations.append((latitude, longitude))

    folium.PolyLine(locations = locations, line_opacity = 1.0, color = 'black').add_to(route_map)
    route_map.save(TRACEROUTE_MAP_FILENAME)  # Save the route map in the folder it is in as 'route_map.html'

    print(f'[+] Saved traceroute map as {TRACEROUTE_MAP_FILENAME}')


if __name__ == '__main__':
    main()
