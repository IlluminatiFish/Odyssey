from odyssey.core.config.config_loader import DISPLAY_TRACKERS, IP_LOGGERS, TRACEROUTE_MAP_FILENAME
from odyssey.core.tracer.trace_route import do_trace
from odyssey.core.utils.utils import get_ssl_cert
from odyssey.core.utils.utils import get_ip_metadata

import ast
import folium


def main():
    param_url = input('[+] URL: ')
    traced_path = do_trace(param_url)

    locations = []

    MAP_CENTER = [0, 0]
    route_map = folium.Map(location=MAP_CENTER, zoom_start=2.5)

    if not traced_path:
        print('[-] No Redirect Traceroute found')
        return

    if len(traced_path.keys()) > 0:
        print()
        print(f'[+] Redirect Traceroute (Size: {len(traced_path.keys())})')
        print()

        count = 1


        locations = []

        for url, trace_data in traced_path.items():

            if url and trace_data:
                ip, server, raw_cookies = trace_data  # Get rid of data delimeter
                cookies = ast.literal_eval(str(raw_cookies))  # Convert our list of type string to a list type again

                # Get all the IP's metadata we will need to use
                ip_data = get_ip_metadata(ip)
                ip_country = ip_data.get('country', 'N/A')

                ip_asn = ip_data.get('as', 'N/A')
                ip_org = ip_data.get('org', 'N/A')
                ip_isp = ip_data.get('isp', 'N/A')
                ip_lat = ip_data.get('lat', -1)
                ip_lon = ip_data.get('lon', -1)

                result = f"[No. {count}]\n\t - Server: {server}\n\t - Country: {ip_country} \n\t - Metadata: {ip}, {ip_asn}, {ip_org}\n\t - URL: {url}"

                # SSL Certificate metadata retrieval
                url_cert = get_ssl_cert(url)

                cert_subject = None

                if url_cert:
                    cert_subject_dict = dict(cert_data[0] for cert_data in url_cert['subject'])
                    cert_subject = cert_subject_dict['commonName']

                    cert_issuer_dict = dict(cert_data[0] for cert_data in url_cert['issuer'])
                    cert_issuer = cert_issuer_dict['commonName']

                    cert_serial = url_cert['serialNumber']

                    result += f'\n\t - SSL Certificate:\n\t\t - Subject: {cert_subject}\n\t\t - Issuer: {cert_issuer}\n\t\t - Serial Number: {cert_serial}'

                # Tracking Cookie retrieval
                if len(cookies) > 0:
                    if DISPLAY_TRACKERS:
                        result += f'\n\t - Tracking Cookies:\n\t\t - Count: {len(cookies)}\n\t\t - Cookie Values:'
                    else:
                        result += f'\n\t - Cookies:\n\t\t - Count: {len(cookies)}\n\t\t - Cookie Values:'
                for cookie in cookies:
                    result += '\n\t\t\t - ' + cookie

                for service in IP_LOGGERS:
                    for name, raw_matchers in service.items():
                        matchers = [dict(raw_matcher) for raw_matcher in raw_matchers]
                        for matcher in matchers:
                            matcher_type, matcher_value = matcher.get('match'), matcher.get('value')

                            match_result = None

                            if matcher_type == 'DOMAIN':
                                match_result = url.split('://')[1].split('/')[0] == matcher_value

                            elif matcher_type == 'DOMAIN_IP':
                                match_result = ip == matcher_value

                            elif matcher_type == 'SSL_CERT_SUBJECT_DOMAIN':
                                match_result = cert_subject == matcher_value

                            if match_result:
                                result += '\n\t - IP Loggers:'
                                result += '\n\t\t\t - ' + name


                print(result)
                print()

                # Route map generation using Folium
                html = f'''
                       <link rel="preconnect" href="https://fonts.gstatic.com">
                       <link href="https://fonts.googleapis.com/css2?family=Space+Mono&display=swap" rel="stylesheet">
                       <p style="font-family: 'Space Mono', monospace;">
                           URL: {url}
                           <br>
                           IP: {ip}
                           <br>
                           ASN: {ip_asn.split(' ')[0]}
                           <br>
                           ORG: {ip_org}
                           <br>
                           ISP: {ip_isp}
                           <br>
                           Tracking Cookies: {len(cookies) > 0}
                           <br>
                       </p>
                   '''

                iframe = folium.IFrame(html, width=600, height=250)
                popup = folium.Popup(iframe)

                # Added to avoid confusion, to see if URL coords are already in list,
                # if so adjust the next URL's coords to be distinct from the previous URL.
                offset = 0.005

                if (ip_lat, ip_lon) in locations:
                    ip_lat, ip_lon = ip_lat + offset, ip_lon + offset

                # Setting up the markers for the FoliumJS map
                START_DATA = (1, 'green')
                BOUNCE_DATA = ([x for x in range(1, len(traced_path.keys()))], 'orange')
                END_DATA = (len(traced_path.keys()), 'red')

                if count == START_DATA[0]:

                    folium.Marker((ip_lat, ip_lon), popup=popup,
                                  icon=folium.Icon(color=START_DATA[1], icon="glyphicon-flash",
                                                   prefix="glyphicon")).add_to(
                        route_map)

                elif count == END_DATA[0]:

                    folium.Marker((ip_lat, ip_lon), popup=popup,
                                  icon=folium.Icon(color=END_DATA[1], icon="glyphicon-flash",
                                                   prefix="glyphicon")).add_to(
                        route_map)
                else:

                    folium.Marker((ip_lat, ip_lon), popup=popup,
                                  icon=folium.Icon(color=BOUNCE_DATA[1], icon="glyphicon-flash",
                                                   prefix="glyphicon")).add_to(route_map)

                locations.append((ip_lat, ip_lon))

                count += 1

    folium.PolyLine(locations=locations, line_opacity=1.0, color='black').add_to(route_map)

    route_map.save(TRACEROUTE_MAP_FILENAME)  # Save the route map in the folder it is in as 'route_map.html'

    print(f'[+] Saved traceroute map as {TRACEROUTE_MAP_FILENAME}')


if __name__ == "__main__":
    main()
