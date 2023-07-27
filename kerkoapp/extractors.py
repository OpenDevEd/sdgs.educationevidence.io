"""
Functions for extracting data from Zotero items.
"""

import re

from kerko.extractors import Extractor


class MatchesTagExtractor(Extractor):
    """Extract a boolean indicating if the item has a tag matching a given regular expression."""

    def __init__(self, *, pattern='', **kwargs):
        super().__init__(**kwargs)
        self.re_pattern = re.compile(pattern) if pattern else None

    def extract(self, item, library_context, spec):
        for tag_data in item.get('data', {}).get('tags', []):
            tag = tag_data.get('tag', '').strip()
            if tag and self.re_pattern.match(tag):
                return True
        return False
