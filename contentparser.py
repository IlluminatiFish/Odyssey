from bs4 import BeautifulSoup
from utils import findURLs, getValue


def processContent(raw_content, url):
    '''
        @:purpose: Processes the raw content found in the doGET(url) function,
                   and find HTML & Header based redirects

        @:param raw_content: The raw content taken from the doGET(url) function.
        @:param url: The URL where the raw content is from.

        @:returns next_url: Returns the next url in the redirect chain.
    '''

    content = raw_content.decode()

    headers = content.split('\r\n\r\n', 1)[0]
    dom_object = content.split('\r\n\r\n', 1)[1]

    header_list = headers.splitlines()

    http_status = int(header_list[:1][0].split(' ')[1])

    http_headers = header_list[1:]

    soup = BeautifulSoup(dom_object, 'html.parser')

    if getValue('Location', http_headers):
        print('[!] Found Location: ', getValue('Location', http_headers))
        return getValue('Location', http_headers)


    meta_tags = soup.findAll('meta')

    if len(meta_tags) > 0:

        urls = []
        for tag in soup.findAll('meta'):
            if tag.get('content') and tag.get('http-equiv') and len(findURLs(tag.get('content'))) > 0:
                url = tag.get('content').split('URL=')[1].replace("'", "")
                urls.append(url)

        if len(urls) > 0:
            unique_urls = set(urls) # Get rid of duplicates
            iterator = iter(unique_urls)
            while True:
                try:
                    url = next(iterator)
                except StopIteration:
                    break
                else:
                    return url
