import re, execjs, socket
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils import get_value, find_urls


def process_content(raw_content, url):
    '''
        Processes the raw content found in the do_get(url) function, and find HTML & Header based redirects

        :param raw_content: The raw content taken from the do_get(url) function.
        :param url: The URL where the raw content is from.

        :returns: The next url in the redirect chain.
    '''

    # Very bad method, as it does not account for all other language characters, needs to be fixed in the future
    content = raw_content.decode('unicode-escape')

    headers = content.split('\r\n\r\n', 1)[0]
    dom_object = content.split('\r\n\r\n', 1)[1]

    header_list = headers.splitlines()

    http_headers = header_list[1:]

    soup = BeautifulSoup(dom_object, 'html.parser')

    # Changed from findAll() to find_all() to iterate over the rest of the tags
    meta_tags = soup.find_all('meta')
    script_lines = soup.find_all('script')

    if get_value('Location', http_headers):
        object = urlparse(get_value('Location', http_headers)).netloc

        ip = None
        domain = None

        object_match = re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', object)

        if object_match != None:
            ip = object
        else:
            domain = object
            domain_ip = None
            try:
                domain_ip = str(socket.gethostbyname(domain))
            except Exception as exc:
                print('[-] An error ocurred in the content parser:\n\n', exc)

        # Fixes a case where the next url was seen to be a local ip / resolved to a local ip in the location header of the previous url
        if ip != '127.0.0.1' and domain_ip != '127.0.0.1':
            return get_value('Location', http_headers)

    if len(meta_tags) > 0:
        urls = []
        for tag in meta_tags:
            if tag.get('content') and tag.get('http-equiv') and len(find_urls(tag.get('content'))) > 0:
                url = str(tag.get('content')).lower().split('url=')[1].replace("'", "") # Quick patch to handle all cases of meta tag formats
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

    if len(script_lines) > 0:

        for script_line in script_lines:


            line_count = len(str(script_line).splitlines())


            if line_count > 1:

                clean_script = str(script_line).splitlines()[1: line_count - 1]
                clean_script = [js.strip() for js in clean_script]

                execution_script = ""


                for js in clean_script:
                    #print('js:', js)

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

                #print(execution_script)

                compiler = execjs.compile(execution_script)

                try:
                    print(compiler.eval(''))
                    return compiler.eval('')
                except Exception:
                    continue # Added a 'continue' statement to iterate over the rest of the scripts found marked by <script> tags


            # Regex pattern to get rid of any HTML tags, better than the old method used
            clean_script = re.sub('<.*?>', '', str(script_line))


            if len(clean_script) > 0:

                script = ""

                if 'window.location.href=' in str(clean_script) and str(clean_script).startswith('window.location.href='):
                    script += clean_script.replace('window.location.href=', 'return ')

                if 'window.location = ' in str(clean_script) and str(clean_script).startswith('window.location = '):
                    script += clean_script.replace('window.location = ', 'return ')

                if 'window.location.replace' in str(clean_script) and str(clean_script).startswith('window.location.replace'):
                    script += clean_script.replace('window.location.replace', 'return ')

                if 'top.location.href=' in str(clean_script) and str(clean_script).startswith('top.location.href='):
                    script += clean_script.replace('top.location.href=', 'return ')


                script += ';'

                compiler = execjs.compile(script)

                try:
                    return compiler.eval('')
                except Exception as ex:
                    continue # Added a 'continue' statement to iterate over the rest of the scripts found marked by <script> tags

            continue
