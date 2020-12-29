import re, execjs
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

    http_status = int(header_list[:1][0].split(' ')[1])

    http_headers = header_list[1:]

    soup = BeautifulSoup(dom_object, 'html.parser')

    meta_tags = soup.findAll('meta')
    script_lines = soup.find_all('script')  # Changed from findAll() to find_all() to iterate over the rest of the scripts found marked by <script> tags


    if get_value('Location', http_headers):
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

                    if 'document.location' in str(js) and str(js).startswith('var'):
                        js = js.replace('document.location', '"' + url + '"')

                    if 'window.location.href =' in str(js) and str(js).startswith('window.location.href ='):
                        js = js.replace('window.location.href =', 'return')

                    if 'window.location.href' in str(js) and str(js).startswith('var'):
                        js = js.replace('window.location.href', '"' + url + '"')

                    if 'document.location.href' in str(js) and str(js).startswith('document.location.href'):
                        js = js.replace('document.location.href =', 'return')
                        
                    if 'document.location.href.replace' in str(js):
                        js = js.replace('document.location.href', '"' + url + '"')

                    execution_script += js + '\n'

                compiler = execjs.compile(execution_script)

                try:
                    return compiler.eval('')
                except Exception as ex:
                    continue # Added a 'continue' statement to iterate over the rest of the scripts found marked by <script> tags


            # Regex pattern to get rid of any HTML tags, better than the old method used
            clean_script = re.sub('<.*?>', '', str(script_line))

            if len(clean_script) > 0:

                script = ""

                if 'window.location.href=' in str(clean_script) and str(clean_script).startswith('window.location.href='):
                    script += clean_script.replace('window.location.href=', 'return ')

                if 'window.location = ' in str(clean_script) and str(clean_script).startswith('window.location = '):
                    script += clean_script.replace('window.location = ', 'return ')

                script += ';'

                compiler = execjs.compile(script)

                try:
                    return compiler.eval('')
                except Exception as ex:
                    continue # Added a 'continue' statement to iterate over the rest of the scripts found marked by <script> tags

            continue
