import re

from typing import Dict, List, Union

from collections import defaultdict


class BodyHandlers:
    @staticmethod
    def _handle_meta_tag(tag) -> Union[Dict[float, List[str]], None]:
        """
        Parse all meta HTML tags that have
        http-equiv set to 'Refresh'.

        Args:
            tag (bs4.element.Tag):
                Raw HTML meta tag.

        Returns:
            If None is returned, no redirects were identified.

            Otherwise, a dictionary of URLs with their associated
            metadata should be returned.
        """

        meta_tag_dict = {}

        DECIMAL_OR_WHOLE = r"(?=.*?\d)\d*[.]?\d*"
        OPTIONAL_MULTI_WHITESPACE = r"(?:\s+)?"

        META_REFRESH_TAG_RE = re.compile(
            f'<meta (content="{DECIMAL_OR_WHOLE}{OPTIONAL_MULTI_WHITESPACE};{OPTIONAL_MULTI_WHITESPACE}(?:url=)?[^,]+" http-equiv=".*"|http-equiv=".*" content="{DECIMAL_OR_WHOLE}{OPTIONAL_MULTI_WHITESPACE};{OPTIONAL_MULTI_WHITESPACE}(?:url=)?[^,]+")(?:/)?>',
            re.IGNORECASE,
        )
        meta_refresh = re.match(META_REFRESH_TAG_RE, str(tag))

        # Meta tag is not a meta refresh, ignore it.
        if not meta_refresh:
            return

        for index, metadata in enumerate(meta_refresh.groups()[0].split(" ")):
            key, value = metadata.split("=", 1)
            meta_tag_dict[key] = value

        required_keys = {"content", "http-equiv"}

        identified_keys = required_keys & set(list(meta_tag_dict.keys()))

        meta_refresh_dict = defaultdict(list)

        if required_keys == identified_keys and tag.get("http-equiv") == "Refresh":

            meta_content = tag.get("content")

            ttr, uri = meta_content.split(";")

            if meta_refresh_dict.get(float(ttr)):
                meta_refresh_dict[float(ttr)].append(uri)
            else:
                meta_refresh_dict[float(ttr)] = [uri]

        return meta_refresh_dict

    def handle_meta_tags(self, tags):

        # Reference: https://en.wikipedia.org/wiki/Meta_refresh
        meta_refreshes = []
        meta_refreshes_dict = defaultdict(list)

        for tag in tags:

            meta_refresh_dict = self._handle_meta_tag(tag)
            meta_refreshes.append(meta_refresh_dict)

        for dict in meta_refreshes:
            for key, value in dict.items():

                if meta_refreshes_dict.get(key):
                    meta_refreshes_dict[key].extend(value)
                else:
                    meta_refreshes_dict[key] = value

        minimum_ttr = min(meta_refreshes_dict, key=float)

        return meta_refreshes_dict.get(minimum_ttr)[-1]
