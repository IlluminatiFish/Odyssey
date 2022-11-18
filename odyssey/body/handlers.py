from typing import Any, Dict, List, Union

from collections import defaultdict

import re
import bs4
import esprima


class RedirectIdentifier(esprima.NodeVisitor):
    """
    An esprima AST NodeVisitor inherited class
    which tries to identify common javascript redirects
    that use literal assignment.

    Attributes:
        redirect_uris: A list of redirect URIs identified.
    """

    def __init__(self):
        self.redirect_uris = []

    def _dictionary_depth(self, dictionary_object: Dict[Any]) -> int:
        """
        Calculates the depth of a given dictionary.

        Args:
            dictionary_object (Dict[Any]):
                A dictionary object.

        Returns:
            If `dictionary_object` is not an instance of a dictionary,
            the depth will be 0.

            Otherwise, the depth of the dictionary as an integer is
            returned.
        """
        if not isinstance(dictionary_object, dict):
            return 0
        else:
            return 1 + (
                max(
                    map(
                        self._dictionary_depth,
                        dictionary_object.values()
                    )
                )
                if dictionary_object else 0
            )

    def visit_CallExpression(self, node: esprima.nodes.CallExpression) -> None:
        """
        An inherited method from the `esprima.NodeVisitor` class,
        it will visit every `CallExpression` along the AST.

        Args:
            node (esprima.nodes.CallExpression):
                A CallExpression object.
        """
        if len(node.arguments) == 1:
            if node.arguments[0].type == 'Literal':
                attribute_depth = self._dictionary_depth(esprima.toDict(node).get('callee')) - 1

                if 'object' in node.callee.object.keys():
                    if (
                            getattr(eval(f'node.callee' + (attribute_depth * '.object')), 'name') in ('window', 'top', 'document')
                            and
                            node.callee.object.property.name == 'location'
                            and
                            node.callee.property.name == 'replace'
                    ):
                        self.redirect_uris.append(node.arguments[0].value)

        self.generic_visit(node)

    def visit_AssignmentExpression(self, node: esprima.nodes.AssignmentExpression) -> None:
        """
        An inherited method from the `esprima.NodeVisitor` class,
        it will visit every `AssignmentExpression` along the AST.

        Args:
            node (esprima.nodes.AssignmentExpression):
                An AssignmentExpression object.
        """
        if node.operator == '=':
            if node.right.type == 'Literal':
                attribute_depth = self._dictionary_depth(esprima.toDict(node).get('left')) - 1

                if 'object' in node.left.object.keys():
                    if (
                            getattr(eval(f'node.left' + (attribute_depth * '.object')), 'name') in ('window', 'top', 'document')
                            and
                            node.left.object.property.name == 'location'
                            and
                            node.left.property.name == 'href'
                    ):
                        self.redirect_uris.append(node.right.value)

                else:
                    if (
                            node.left.object.name in ('window', 'top', 'document')
                            and
                            node.left.property.name == 'location'
                    ):
                        self.redirect_uris.append(node.right.value)

        self.generic_visit(node)


class BodyHandlers:
    @staticmethod
    def _handle_meta_tag(tag: bs4.element.Tag) -> Union[Dict[float, List[str]], None]:
        """
        Parse all meta HTML tag that have
        http-equiv set to 'Refresh'.

        Args:
            tag (bs4.element.Tag):
                A BeautifulSoup4 Tag object.

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

        # Meta tag is not a meta refresh, pass on a None value.
        if not meta_refresh:
            return None

        for metadata in meta_refresh.groups()[0].split(" "):
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

    @staticmethod
    def handle_javascript(script: str) -> str:
        """
        Identifies simple literal assignment
        redirects present in in-line scripts.

        Args:
            script (str):
                A string representation of the script.

        Returns:
            The next URI in the redirect chain as a string
        """
        tree = esprima.parse(script)

        redirect_identifier = RedirectIdentifier()
        redirect_identifier.visit(tree)

        redirect_uri = redirect_identifier.redirect_uris[-1] if len(
            redirect_identifier.redirect_uris
            ) != 0 else None

        return redirect_uri

    def handle_meta_tags(self, tags: List[bs4.element.Tag]) -> Union[str, None]:
        """
        Parse all meta HTML tags that have
        http-equiv set to 'Refresh'.

        Args:
            tags (List[bs4.element.Tag]):
                A BeautifulSoup4 Tag object.

        Returns:
            The next URI in the redirect chain as a string
        """

        # Reference: https://en.wikipedia.org/wiki/Meta_refresh
        meta_refreshes = []
        meta_refreshes_dict = defaultdict(list)

        for tag in tags:

            meta_refresh_dict = self._handle_meta_tag(tag)

            # Prevents meta tags that are not in the format of the meta refresh tags
            if not meta_refresh_dict:
                break

            meta_refreshes.append(meta_refresh_dict)

        for meta_refresh in meta_refreshes:
            for key, value in meta_refresh.items():

                if meta_refreshes_dict.get(key):
                    meta_refreshes_dict[key].extend(value)
                else:
                    meta_refreshes_dict[key] = value

        # This variable will be an empty dictionary if no meta refreshes are found
        if not meta_refreshes_dict:
            return None

        minimum_ttr = min(meta_refreshes_dict, key=float)
        return meta_refreshes_dict.get(minimum_ttr)[-1]
