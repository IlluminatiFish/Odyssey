from odyssey.core.utils.utils import HeaderUtils, find_urls

from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ipaddress import ip_address

import re
import socket
import magic
import execjs

class ResponseParser:

    def __init__(self, raw_response, response_url):
        self.raw_response = raw_response
        self.response_url = response_url

    def parse(self):

        raw_headers = self.raw_response.split(b'\r\n\r\n', 1)[0].decode()


        header_list = raw_headers.splitlines()

        response_headers = header_list[1:]

        header_utils = HeaderUtils(response_headers)

        content_type = header_utils.get_value('Content-Type')

        refresh_value = header_utils.get_value('Refresh')
        location_value = header_utils.get_value('Location')

        if refresh_value:

            if 'url=' in refresh_value.lower():

                parition = re.split('URL=', refresh_value, flags=re.IGNORECASE)
                url = parition[1]

                return url

        if location_value:

            location_value_host = urlparse(location_value).netloc

            ip = None
            domain_ip = None

            is_ip = re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', location_value_host)

            # Host in the location header is an IP
            if is_ip:
                ip = location_value_host
            else: # Host in the location header is a domain
                try:
                    domain_ip = str(socket.gethostbyname(location_value_host))
                except Exception as error:
                    print(f'[ERROR] (RESPONSE_PARSER) Could not resolve {location_value_host} to an IP')

            # Fixes cases where the location header gave/resolved to a non-routeable ip address
            if (ip and ip_address(ip).is_global) or (domain_ip and ip_address(domain_ip).is_global):
                return header_utils.get_value('Location')


        # HTML-based redirect checks

        #
        # I had a thought in when working on Odyssey and asked myself the following question:
        #
        # Q: Can we trust that the content type header of the response is true and valid for the data in the response body?
        #
        # A: No! We can't just blindly trust any server on the internet, therefore we employ a method to double check
        #    that the mimetype set by the server in the content-type header is what it is being advertised as,
        #    prevents weird edge cases that could've occurred here
        #

        # Reference: https://stackoverflow.com/a/43049834

        magician = magic.Magic(mime=True)


        true_mimetype = magician.from_buffer(self.raw_response)

        if not content_type:
            content_type = true_mimetype

        else:
            # Raw content-type header could include parameters there we split at the first
            # separator (semi-colon) we see to extract the mimetype of the content
            content_mimetype = content_type.split(";")[0]

            # If the content types are not the same, trust the mimetype from the python-magic library instead of the server
            if str(true_mimetype) != str(content_mimetype):
                content_type = true_mimetype


        # Grab all details if provided in the content-type header and parse them into a dictionary for easy access later on
        raw_details = content_type.split(";")[1:]
        details = [raw_detail.strip() for raw_detail in raw_details]

        details_dict = {}
        for detail in details:
            parameter, value = detail.split("=")
            details_dict[parameter] = value

        # If content-type is not text/html then reject parsing it
        if not content_type.startswith("text/html"):
            return

        # Uses the charset given in the content-type header if not found it uses cp437 encoding by default
        decode_charset = details_dict.get('charset', 'cp437')

        raw_response = self.raw_response.decode(decode_charset)

        response_dom = raw_response.split('\r\n\r\n', 1)[1]

        soup = BeautifulSoup(response_dom, 'html.parser')

        meta_tags = soup.find_all('meta')
        script_tags = soup.find_all('script')


        # Meta tag based redirects

        if len(meta_tags) > 0:

            for meta_tag in meta_tags:
                if meta_tag.get('content') and meta_tag.get('http-equiv') and len(find_urls(meta_tag.get('content'))) > 0:

                    parition = re.split('URL=', meta_tag.get('content'), flags=re.IGNORECASE)
                    url = parition[1].replace("'", "")

                    return url

        # Inline Javascript based redirects
        if len(script_tags) > 0:

            for script_tag in script_tags:

                script_line_count = len(str(script_tag).splitlines())

                if script_line_count > 1:

                    clean_script = str(script_tag).splitlines()[1: script_line_count - 1]
                    clean_script = [js.strip() for js in clean_script]

                    execution_script = ""

                    for js in clean_script:

                        if 'document.location' in str(js) and str(js).startswith('var'):
                            js = js.replace('document.location', '"' + self.response_url + '"')

                        if 'window.location=' in str(js) and str(js).startswith('window.location='):
                            js = js.replace('window.location=', 'return ')

                        if 'window.location.href =' in str(js) and str(js).startswith('window.location.href ='):
                            js = js.replace('window.location.href =', 'return')

                        if 'window.location.href' in str(js) and str(js).startswith('var'):
                            js = js.replace('window.location.href', '"' + self.response_url + '"')

                        if 'document.location.href' in str(js) and str(js).startswith('document.location.href'):
                            js = js.replace('document.location.href =', 'return')

                        if 'document.location.href.replace' in str(js):
                            js = js.replace('document.location.href', '"' + self.response_url + '"')

                        if 'window.location.replace' in str(js) and str(js).startswith('window.location.replace'):
                            js = js.replace('window.location.replace', 'return ')

                        execution_script += js + '\n'

                    compiler = execjs.compile(execution_script)

                    try:
                        return compiler.eval('')
                    except Exception:
                        # Added a 'continue' statement to iterate over the rest of the scripts found marked by <script> tags
                        continue

                # Regex pattern to get rid of any HTML tags, better than the old method used
                clean_script = re.sub('<.*?>', '', str(script_tag))

                if len(clean_script) > 0:

                    script = ""

                    if 'window.location.href=' in str(clean_script) and str(clean_script).startswith(
                            'window.location.href='):
                        script += clean_script.replace('window.location.href=', 'return ')

                    if 'window.location = ' in str(clean_script) and str(clean_script).startswith('window.location = '):
                        script += clean_script.replace('window.location = ', 'return ')

                    if 'window.location.replace' in str(clean_script) and str(clean_script).startswith(
                            'window.location.replace'):
                        script += clean_script.replace('window.location.replace', 'return ')

                    if 'top.location.href=' in str(clean_script) and str(clean_script).startswith('top.location.href='):
                        script += clean_script.replace('top.location.href=', 'return ')

                    script += ';'

                    compiler = execjs.compile(script)

                    try:
                        return compiler.eval('')
                    except Exception:
                        # Added a 'continue' statement to iterate over the rest of the scripts found marked by <script> tags
                        continue
                continue
