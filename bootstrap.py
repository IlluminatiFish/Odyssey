import ast, folium

from odyssey.core.tracer.trace_path import do_trace
from odyssey.core.utils.get_certs import get_ssl_cert
from odyssey.core.utils.get_ip_data import get_ip_data


def main():
    param_url = input('[+] URL: ')
    traced_path = do_trace(param_url)

    if len(traced_path.keys()) > 0:
        print()
        print(f'[+] Redirect Traceroute (Size: {len(traced_path.keys())})')
        print()

        count = 1

        MAP_CENTER = [0, 0]
        route_map = folium.Map(location=MAP_CENTER, zoom_start=2.5)

        locations = []

        for url, trace_data in traced_path.items():


            if url and trace_data:
                data = trace_data.split('**') # Get rid of data delimeter
                ip = data[0]
                server = data[1]
                tracking_cookies = ast.literal_eval(str(data[2])) # Convert our list of type string to a list type again

                # Get all the IP's metadata we will need to use
                ip_data = get_ip_data(ip)
                ip_country = ip_data['country']

                ip_asn = ip_data['as']
                ip_org = ip_data['org']
                ip_isp = ip_data['isp']
                ip_lat = ip_data['lat']
                ip_lon = ip_data['lon']


                result = f"[No. {count}]\n\t - Server: {server}\n\t - Country: {ip_country} \n\t - Metadata: {ip}, {ip_asn}, {ip_org}\n\t - URL: {url}"


               # SSL Certificate metadata retrieval
                url_cert = get_ssl_cert(url)
                if url_cert:
                    cert_subject_dict = dict(cert_data[0] for cert_data in url_cert['subject'])
                    cert_subject = cert_subject_dict['commonName']

                    cert_issuer_dict = dict(cert_data[0] for cert_data in url_cert['issuer'])
                    cert_issuer = cert_issuer_dict['commonName']

                    cert_serial = url_cert['serialNumber']

                    result += f'\n\t - SSL Certificate:\n\t\t - Subject: {cert_subject}\n\t\t - Issuer: {cert_issuer}\n\t\t - Serial Number: {cert_serial}'

                # Tracking Cookie retrieval
                if len(tracking_cookies) > 0:
                    result += f'\n\t - Tracking Cookies:\n\t\t - Count: {len(tracking_cookies)}\n\t\t - Cookie Value:'
                for tracking_cookie in tracking_cookies:
                    result += '\n\t\t\t - ' + tracking_cookie

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
                                  icon=folium.Icon(color=START_DATA[1], icon="glyphicon-flash", prefix="glyphicon")).add_to(
                        route_map)
                elif count == END_DATA[0]:
                    folium.Marker((ip_lat, ip_lon), popup=popup,
                                  icon=folium.Icon(color=END_DATA[1], icon="glyphicon-flash", prefix="glyphicon")).add_to(
                        route_map)
                else:
                    folium.Marker((ip_lat, ip_lon), popup=popup, icon=folium.Icon(color=BOUNCE_DATA[1], icon="glyphicon-flash",
                                                                            prefix="glyphicon")).add_to(route_map)

                locations.append((ip_lat, ip_lon))

                count += 1


    folium.PolyLine(locations=locations, line_opacity=1.0, color='black').add_to(route_map)

    route_map.save('route_map.html')  # Save the route map in the folder it is in as 'route_map.html'


main()