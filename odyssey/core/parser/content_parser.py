from odyssey.core.requestor.requestor import make_request
from odyssey.core.utils.odyssey_utils import get_value, find_urls

from urllib.parse import urlparse
from bs4 import BeautifulSoup

import re, execjs, socket, magic


def process_response(raw_content, url):
    '''
        Processes the raw response received, and find HTML & Header based redirects

        :param raw_content: The raw response from the socket.
        :param url: The URL where the raw response is from.

        :returns: The next url in the redirect chain.
    '''

    # Very bad method, as it does not account for all other language characters, needs to be fixed in the future

    headers = raw_content.split(b'\r\n\r\n', 1)[0].decode()

    header_list = headers.splitlines()

    http_headers = header_list[1:]

    content_type = get_value('Content-Type', http_headers)

    # Header-based redirect checks

    # Check for 'Refresh' headers from websites such as Instagram that redirect out of Instagram
    if get_value('Refresh', http_headers):

        refresh_header_object = get_value('Refresh', http_headers)

        if 'url=' in refresh_header_object.lower():
            # Fixes case sensitivity issues from the extracted url
            regex_split = re.split('URL=', refresh_header_object, flags=re.IGNORECASE)
            url = regex_split[1]

            return url

    if get_value('Location', http_headers):
        location_header_netloc = urlparse(get_value('Location', http_headers)).netloc

        ip = None
        domain = None

        location_header_object_match = re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', location_header_netloc)

        if location_header_object_match is not None:
            ip = location_header_netloc
        else:
            domain = location_header_netloc
            domain_ip = None

            try:
                domain_ip = str(socket.gethostbyname(domain))
            except Exception as error:
                print('[-] An error occurred in the content parser:\n\n', error)

        # Fixes a case where the next url was seen to be a local ip / resolved to a local ip in the location header of the previous url
        if ip != '127.0.0.1' and domain_ip != '127.0.0.1':
            return get_value('Location', http_headers)

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

    # Raw content-type header could include parameters there we split at the first
    # separator (semi-colon) we see to extract the mimetype of the content
    content_mimetype = content_type.split(";")[0]

    # Will probably rewrite this part later to use our own built-in methods to send requests to the URL to retrive the
    # content at the URL

    raw_response = make_request(url)
    raw_response_body = raw_response.split(b'\r\n\r\n')[1]

    magician = magic.Magic(mime=True)
    true_mimetype = magician.from_buffer(raw_response_body)

    # If the content types are not the same, trust the mimetype from the python-magic library instead of the server
    if str(true_mimetype) != str(content_mimetype):
        content_type = true_mimetype

    # Grab all details if provided in the content-type header and parse them into a dictionary for easy access later on
    raw_details = content_type.split(";")[1:]
    details = [raw_detail.strip() for raw_detail in raw_details]

    details_dict = {}
    for detail in details:
        parameter = detail.split("=")[0]
        value = detail.split("=")[1]
        details_dict[parameter] = value

    # If content-type is not text/html then reject parsing it
    if not content_type.startswith("text/html"):
        return

    # Uses the charset given in the content-type header if not found it uses cp437 encoding by default
    decode_charset = details_dict.get('charset', 'cp437')

    content = raw_content.decode(decode_charset)

    dom_object = content.split('\r\n\r\n', 1)[1]

    soup = BeautifulSoup(dom_object, 'html.parser')

    # Changed from findAll() to find_all() to iterate over the rest of the tags
    meta_tags = soup.find_all('meta')
    script_lines = soup.find_all('script')

    # Meta tag redirects

    if len(meta_tags) > 0:
        urls = []
        for tag in meta_tags:
            if tag.get('content') and tag.get('http-equiv') and len(find_urls(tag.get('content'))) > 0:
                # Fixes case sensitivity issues from the extracted url
                regex_split = re.split('URL=', tag.get('content'), flags=re.IGNORECASE)
                url = regex_split[1].replace("'", "")

                urls.append(url)

        if len(urls) > 0:
            unique_urls = set(urls)  # Get rid of duplicates
            iterator = iter(unique_urls)
            while True:
                try:
                    url = next(iterator)
                except StopIteration:
                    break
                else:
                    return url

    # Inline Javascript redirects

    if len(script_lines) > 0:

        for script_line in script_lines:

            line_count = len(str(script_line).splitlines())

            if line_count > 1:

                clean_script = str(script_line).splitlines()[1: line_count - 1]
                clean_script = [js.strip() for js in clean_script]

                execution_script = ""

                for js in clean_script:

                    if 'document.location' in str(js) and str(js).startswith('var'):
                        js = js.replace('document.location', '"' + url + '"')

                    if 'window.location=' in str(js) and str(js).startswith('window.location='):
                        js = js.replace('window.location=', 'return ')

                    if 'window.location.href =' in str(js) and str(js).startswith('window.location.href ='):
                        js = js.replace('window.location.href =', 'return')

                    if 'window.location.href' in str(js) and str(js).startswith('var'):
                        js = js.replace('window.location.href', '"' + url + '"')

                    if 'document.location.href' in str(js) and str(js).startswith('document.location.href'):
                        js = js.replace('document.location.href =', 'return')

                    if 'document.location.href.replace' in str(js):
                        js = js.replace('document.location.href', '"' + url + '"')

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
            clean_script = re.sub('<.*?>', '', str(script_line))

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
