import ast, socket, ssl, time, folium
from urllib.parse import urlparse

from contentparser import process_content
from utils import get_data, get_server, get_cookies, get_ssl_cert

VISITED = {}
SEGMENT_BUFFER = 8192 # How big you want each sock.recv() call to take byte-wise
TIMEOUT = 10
ua = "Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0"


def do_get(url):
    '''
        Sends a correctly formed HTTP 'GET' request using sockets, to get content from the web server.

        :param url: The URL where you want to get the content from.

        :returns: Returns the raw bytes response from the web server.
    '''

    if url is not None:



        scheme = str(urlparse(url).scheme)
        domain = str(urlparse(url).netloc)

        root = scheme + '://' + domain


        if domain:
            if ':' in domain: # Catches ports in the netloc from urlparse (Ex. some.domain:xxxx)
                domain = domain.split(':')[0]

            raw_path = url.split('://')[1].split('/', 1)[1] if len(url.split('://')[1].split('/')) > 1 else ""

            path = raw_path # Set current path to the raw_path

            if urlparse(raw_path).query:

                path = urlparse(raw_path).path + '?' + urlparse(raw_path).query

                if urlparse(raw_path).fragment:
                    path = path + '#' + urlparse(raw_path).fragment

            if urlparse(raw_path).fragment: # If we have a fragement in the URL such as (https://bit.ly/37O7zEf#HJEDY_BRMFE_6PIHS) we should get rid of it
                path = path.split('#')[0]

            port = 80 if scheme == "http" else 443

            sock = socket.socket()

            request = "GET /{} HTTP/1.1\r\nHost: {}\r\nAccept: */*\r\nConnection: close\r\nUser-Agent: {}\r\n\r\n".format(
                path, domain, ua)

            if scheme == 'http':
                sock.connect((domain, port))

                sock.send(request.encode())

                sock.settimeout(TIMEOUT)  # Default socket operation timeout of 2 seconds

                raw_response = bytes("".encode())

                while True:
                    try:
                        segment = sock.recv(SEGMENT_BUFFER)
                    except socket.timeout as ex:
                        print('[-] Socket receiver timed out after {} seconds'.format(TIMEOUT))
                        break
                    if not segment:
                        break
                    raw_response += bytes(segment)

                VISITED[url] = socket.gethostbyname(domain) + '**' + get_server(raw_response) + '**' + get_cookies(raw_response, True)
                print()
                print('[HTTP] CURRENT_URL:', url)
                next_url = process_content(raw_response, url)
                print('[HTTP] NEXT_URL:', next_url)
                print()

                if next_url is not None:
                    '''
                        If the current url & next url are the same then do not accept
                    '''
                    if url != next_url:

                        '''
                            Fixes the script going into an endless loop of the same redirects
                        '''
                        if next_url not in VISITED.keys():

                            if next_url.startswith('/'):  # Local page redirects caught by this
                                do_get(root + next_url)

                            do_get(next_url)
                        else:
                            return



                sock.close()

            if scheme == 'https':
                context = ssl.SSLContext()
                ssl_sock = context.wrap_socket(sock, server_hostname=domain)
                try:
                    ssl_sock.connect((domain, port))
                except socket.gaierror as ex:
                    print('[-] Failed to resolve domain ({})'.format(domain))
                    return



                ssl_sock.send(request.encode())

                ssl_sock.settimeout(TIMEOUT) # Default socket operation timeout of 2 seconds

                raw_response = bytes("".encode())

                while True:
                    try:
                        segment = ssl_sock.recv(SEGMENT_BUFFER)
                    except socket.timeout as ex:
                        print('[-] Socket receiver timed out after {} seconds'.format(TIMEOUT))
                        break

                    if not segment:
                        break
                    raw_response += bytes(segment)

                VISITED[url] = socket.gethostbyname(domain) + '**' + get_server(raw_response) + '**' + get_cookies(raw_response, True)
                print()
                print('[HTTPS] CURRENT_URL:', url)
                next_url = process_content(raw_response, url)
                print('[HTTPS] NEXT_URL:', next_url)
                print()


                if next_url is not None:
                    '''
                        If the current url & next url are the same then do not accept
                    '''
                    if url != next_url:

                        '''
                            Fixes the script going into an endless loop of the same redirects
                        '''
                        if next_url not in VISITED.keys():

                            if next_url.startswith('/'): # Local page redirects caught by this
                                do_get(root + next_url)

                            do_get(next_url)
                        else:
                            return

                ssl_sock.close()


URL = input('[*] URL: ')
do_get(URL)




if len(VISITED.keys()) > 0:
    print()
    print('[+] Redirect Traceroute (Size: {})'.format(len(VISITED.keys())))
    print()

    count = 1

    MAP_CENTER = [0, 0]
    route_map = folium.Map(location=MAP_CENTER, zoom_start=2.5)

    locations = []


    for url, msg in VISITED.items():

        time.sleep(10) # This is needed as IP-API is rate-limited to a certain amount of requests per minute (which is 45 I believe)
        if url and msg:

            data = msg.split('**') # Get rid of data delimeter
            ip = data[0]
            server = data[1]
            tracking_cookies = ast.literal_eval(str(data[2])) # Convert our list of type string to a list type again

            result = "[No. {}]\n\t - Server: {}\n\t - Country: {} \n\t - Metadata: {}, {}, {}\n\t - URL: {}".format(count, server, get_data(ip, 'country'), ip, get_data(ip, 'as'), get_data(ip, 'org'), url)

            # SSL Certificate metadata retrieval
            url_cert = get_ssl_cert(url)
            if url_cert:

                cert_subject_dict = dict(cert_data[0] for cert_data in url_cert['subject'])
                cert_subject = cert_subject_dict['commonName']

                cert_issuer_dict = dict(cert_data[0] for cert_data in url_cert['issuer'])
                cert_issuer = cert_issuer_dict['commonName']

                cert_serial = url_cert['serialNumber']

                result += '\n\t - SSL Certificate:\n\t\t - Subject: {}\n\t\t - Issuer: {}\n\t\t - Serial Number: {}'.format(cert_subject, cert_issuer, cert_serial)

            # Tracking Cookie retrieval
            if len(tracking_cookies) > 0:
                result += '\n\t - Tracking Cookies:\n\t\t - Count: {}\n\t\t - Cookie Value:'.format(len(tracking_cookies))

            for tracking_cookie in tracking_cookies:
                result += '\n\t\t\t - ' + tracking_cookie

            print(result)
            print()

            # Route map generation using Folium
            html = '''
                <link rel="preconnect" href="https://fonts.gstatic.com">
                <link href="https://fonts.googleapis.com/css2?family=Space+Mono&display=swap" rel="stylesheet">
                <p style="font-family: 'Space Mono', monospace;">
                    URL: {}
                    <br>
                    IP: {}
                    <br>
                    ASN: {}
                    <br>
                    ORG: {}
                    <br>
                    ISP: {}
                </p>
            '''.format(url, ip, get_data(ip, 'as').split(' ')[0], get_data(ip, 'org'), get_data(ip, 'isp'))

            iframe = folium.IFrame(html, width=600, height=250)
            popup = folium.Popup(iframe)

            lat = get_data(ip, 'lat')
            lon = get_data(ip, 'lon')

            # Added to avoid confusion, to see if URL coords are already in list,
            # if so adjust the next URL's coords to be distinct from the previous URL.
            offset = 0.005

            if (lat, lon) in locations:
                lat, lon = lat + offset, lon + offset

            START_DATA = (1, 'green')
            BOUNCE_DATA = ([x for x in range(1, len(VISITED.keys()))], 'orange')
            END_DATA = (len(VISITED.keys()), 'red')



            if count == START_DATA[0]:
                folium.Marker((lat, lon), popup=popup, icon=folium.Icon(color=START_DATA[1], icon="glyphicon-flash", prefix="glyphicon")).add_to(route_map)
            elif count == END_DATA[0]:
                folium.Marker((lat, lon), popup=popup, icon=folium.Icon(color=END_DATA[1], icon="glyphicon-flash", prefix="glyphicon")).add_to(route_map)
            else:
                folium.Marker((lat, lon), popup=popup, icon=folium.Icon(color=BOUNCE_DATA[1], icon="glyphicon-flash", prefix="glyphicon")).add_to(route_map)


            locations.append((lat, lon))

            count += 1

folium.PolyLine(locations=locations, line_opacity=0.5, color='black').add_to(route_map)

route_map.save('route_map.html') #Save the route map in the folder it is in as 'route_map.html'
