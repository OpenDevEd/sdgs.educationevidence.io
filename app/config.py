import pathlib
import re

from environs import Env
from flask_babel import gettext as _
from kerko import extractors, transformers
from kerko.composer import Composer
from kerko.renderers import TemplateRenderer
from kerko.specs import BadgeSpec, CollectionFacetSpec, FieldSpec, SortSpec
from whoosh.fields import BOOLEAN, STORED

from .extractors import MatchesTagExtractor
from .transformers import extra_field_cleaner

# pylint: disable=invalid-name

env = Env()
env.read_env()


class Config():

    def __init__(self):
        app_dir = pathlib.Path(env.str('FLASK_APP')).parent.absolute()

        # Get configuration values from the environment.
        self.SECRET_KEY = env.str('SECRET_KEY')
        self.KERKO_ZOTERO_API_KEY = env.str('KERKO_ZOTERO_API_KEY')
        self.KERKO_ZOTERO_LIBRARY_ID = env.str('KERKO_ZOTERO_LIBRARY_ID')
        self.KERKO_ZOTERO_LIBRARY_TYPE = env.str('KERKO_ZOTERO_LIBRARY_TYPE')
        self.KERKO_DATA_DIR = env.str('KERKO_DATA_DIR', str(app_dir / 'data' / 'kerko'))

        # Set other configuration variables.
        self.LOGGING_HANDLER = 'default'
        self.EXPLAIN_TEMPLATE_LOADING = False

        self.LIBSASS_INCLUDES = [
            str(pathlib.Path(__file__).parent.parent / 'static' / 'src' / 'vendor' / 'bootstrap' / 'scss'),
            str(pathlib.Path(__file__).parent.parent / 'static' / 'src' / 'vendor' / '@fortawesome' / 'fontawesome-free' / 'scss'),
        ]

        self.BABEL_DEFAULT_LOCALE = 'en_GB'
        self.KERKO_WHOOSH_LANGUAGE = 'en'
        self.KERKO_ZOTERO_LOCALE = 'en-GB'

        self.HOME_URL = 'https://opendeved.net'
        self.HOME_TITLE = _("Open Development & Education")
        # self.HOME_SUBTITLE = _("...")

        self.ABOUT_URL = 'https://opendeved.net/about/'
        self.PARTNERS_URL = 'https://opendeved.net/partners/'
        self.BLOG_URL = 'https://opendeved.net/blog/'
        self.JOBS_URL = 'https://opendeved.net/jobs/'
        self.PROGRAMMES_URL = 'https://opendeved.net/programmes/'
        self.CONTACTUS_URL = 'https://opendeved.net/contact-us/'

        self.NAV_TITLE = _("Evidence Library")
        self.KERKO_TITLE = _("Evidence Library – Open Development & Education")
        self.KERKO_PRINT_ITEM_LINK = True
        self.KERKO_PRINT_CITATIONS_LINK = True
        self.KERKO_RESULTS_FIELDS = ['id', 'attachments', 'bib', 'coins', 'data', 'preview', 'url']
        self.KERKO_RESULTS_ABSTRACTS = True
        self.KERKO_RESULTS_ABSTRACTS_MAX_LENGTH = 500
        self.KERKO_RESULTS_ABSTRACTS_MAX_LENGTH_LEEWAY = 40
        self.KERKO_TEMPLATE_LAYOUT = 'app/layout.html.jinja2'
        self.KERKO_TEMPLATE_SEARCH = 'app/search.html.jinja2'
        self.KERKO_TEMPLATE_SEARCH_ITEM = 'app/search-item.html.jinja2'
        self.KERKO_TEMPLATE_ITEM = 'app/item.html.jinja2'
        self.KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW = True
        self.KERKO_RELATIONS_INITIAL_LIMIT = 50

        # CAUTION: The URL's query string must be changed after any edit to the CSL
        # style, otherwise zotero.org might still use a previously cached version of
        # the file.
        self.KERKO_CSL_STYLE = 'https://docs.opendeved.net/static/dist/csl/eth_apa.xml?202012301815'

        self.KERKO_COMPOSER = Composer(
            whoosh_language=self.KERKO_WHOOSH_LANGUAGE,
            exclude_default_facets=['facet_tag', 'facet_link', 'facet_item_type'],
            exclude_default_fields=['data'],
            default_item_exclude_re=r'^_exclude$',
            default_child_include_re=r'^(_publish|publishPDF)$',
            default_child_exclude_re=r'',
        )

        # Replace the default 'data' extractor to strip unwanted data from the Extra field.
        self.KERKO_COMPOSER.add_field(
            FieldSpec(
                key='data',
                field_type=STORED,
                extractor=extractors.TransformerExtractor(
                    extractor=extractors.RawDataExtractor(),
                    transformers=[extra_field_cleaner]
                ),
            )
        )

        # Add field for storing the formatted item preview used on search result
        # pages. This relies on the CSL style's in-text citation formatting and only
        # makes sense using our custom CSL style!
        self.KERKO_COMPOSER.add_field(
            FieldSpec(
                key='preview',
                field_type=STORED,
                extractor=extractors.TransformerExtractor(
                    extractor=extractors.ItemExtractor(key='citation', format_='citation'),
                    # Zotero wraps the citation in a <span> element (most probably
                    # because it expects the 'citation' format to be used in-text),
                    # but that <span> has to be removed because our custom CSL style
                    # causes <div>s to be nested within. Let's replace that <span>
                    # with the same markup that the 'bib' format usually provides.
                    transformers=[
                        lambda value: re.sub(r'^<span>', '<div class="csl-entry">', value, count=1),
                        lambda value: re.sub(r'</span>$', '</div>', value, count=1),
                    ]
                )
            )
        )

        # Add extractors for the 'alternate_id' field.
        self.KERKO_COMPOSER.fields['alternate_id'].extractor.extractors.append(
            extractors.TransformerExtractor(
                extractor=extractors.ItemDataExtractor(key='extra'),
                transformers=[
                    transformers.find(
                        regex=r'^\s*EdTechHub.ItemAlsoKnownAs\s*:\s*(.*)$',
                        flags=re.IGNORECASE | re.MULTILINE,
                        max_matches=1,
                    ),
                    transformers.split(sep=';'),
                ]
            )
        )
        self.KERKO_COMPOSER.fields['alternate_id'].extractor.extractors.append(
            extractors.TransformerExtractor(
                extractor=extractors.ItemDataExtractor(key='extra'),
                transformers=[
                    transformers.find(
                        regex=r'^\s*KerkoCite.ItemAlsoKnownAs\s*:\s*(.*)$',
                        flags=re.IGNORECASE | re.MULTILINE,
                        max_matches=1,
                    ),
                    transformers.split(sep=' '),
                ]
            )
        )
        self.KERKO_COMPOSER.fields['alternate_id'].extractor.extractors.append(
            extractors.TransformerExtractor(
                extractor=extractors.ItemDataExtractor(key='extra'),
                transformers=[
                    transformers.find(
                        regex=r'^\s*shortDOI\s*:\s*(\S+)\s*$',
                        flags=re.IGNORECASE | re.MULTILINE,
                        max_matches=0,
                    ),
                ]
            )
        )

        self.KERKO_COMPOSER.add_facet(
            CollectionFacetSpec(
                key='facet_featured',
                filter_key='featured',
                title=_('Featured publisher'),
                weight=10,
                collection_key='JUDM2WBF',
            )
        )

        self.KERKO_COMPOSER.add_facet(
            CollectionFacetSpec(
                key='facet_pubtype',
                filter_key='pubtype',
                title=_('Publication type'),
                weight=20,
                collection_key='NEH6ARC4',
            )
        )

        self.KERKO_COMPOSER.add_facet(
            CollectionFacetSpec(
                key='facet_theme',
                filter_key='theme',
                title=_('Theme'),
                weight=30,
                collection_key='QK8NXPKZ',
            )
        )

        self.KERKO_COMPOSER.add_facet(
            CollectionFacetSpec(
                key='facet_location',
                filter_key='location',
                title=_('Location'),
                weight=50,
                collection_key='94GNF2EB',
            )
        )

        # OpenDevEd flag and badge.
        self.KERKO_COMPOSER.add_field(
            FieldSpec(
                key='opendeved',
                field_type=BOOLEAN(stored=True),
                extractor=extractors.InCollectionExtractor(collection_key='JG6T4YVA'),
            )
        )
        self.KERKO_COMPOSER.add_badge(
            BadgeSpec(
                key='opendeved',
                field=self.KERKO_COMPOSER.fields['opendeved'],
                activator=lambda field, item: bool(item.get(field.key)),
                renderer=TemplateRenderer(
                    'app/_ode-badge.html.jinja2', badge_title=_('Published by Open Development & Education')
                ),
                weight=100,
            )
        )
        # "Internal document" flag and badge.
        self.KERKO_COMPOSER.add_field(
            FieldSpec(
                key='internal',
                field_type=BOOLEAN(stored=True),
                extractor=MatchesTagExtractor(pattern=r'^_internal$'),
            )
        )
        self.KERKO_COMPOSER.add_badge(
            BadgeSpec(
                key='internal',
                field=self.KERKO_COMPOSER.fields['internal'],
                activator=lambda field, item: item.get(field.key, False),
                renderer=TemplateRenderer(
                    'app/_text-badge.html.jinja2', text=_('Internal<br />document')
                ),
                weight=10,
            )
        )
        # "Coming soon" flag and badge.
        self.KERKO_COMPOSER.add_field(
            FieldSpec(
                key='comingsoon',
                field_type=BOOLEAN(stored=True),
                extractor=MatchesTagExtractor(pattern=r'^_comingsoon$'),
            )
        )
        self.KERKO_COMPOSER.add_badge(
            BadgeSpec(
                key='comingsoon',
                field=self.KERKO_COMPOSER.fields['comingsoon'],
                activator=lambda field, item: item.get(field.key, False),
                renderer=TemplateRenderer(
                    'app/_text-badge.html.jinja2', text=_('Coming<br >soon')
                ),
                weight=20,
            )
        )

        # Sort option based on the OpenDevEd flag.
        self.KERKO_COMPOSER.add_sort(
            SortSpec(
                key='ode_desc',
                label=_('Open Development & Education first'),
                weight=100,
                fields=[
                    self.KERKO_COMPOSER.fields['opendeved'],
                    self.KERKO_COMPOSER.fields['sort_date'],
                    self.KERKO_COMPOSER.fields['sort_creator'],
                    self.KERKO_COMPOSER.fields['sort_title']
                ],
                reverse=[
                    False,
                    True,
                    False,
                    False,
                ],
            )
        )


class DevelopmentConfig(Config):

    def __init__(self):
        super().__init__()

        self.CONFIG = 'development'
        self.DEBUG = True
        self.ASSETS_DEBUG = env.bool('ASSETS_DEBUG', True)  # Don't bundle/minify static assets.
        self.LIBSASS_STYLE = 'expanded'
        self.LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'DEBUG')


class ProductionConfig(Config):

    def __init__(self):
        super().__init__()

        self.CONFIG = 'production'
        self.DEBUG = False
        self.ASSETS_DEBUG = env.bool('ASSETS_DEBUG', False)
        self.ASSETS_AUTO_BUILD = False
        self.LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'WARNING')
        self.GOOGLE_ANALYTICS_ID = 'UA-169419325-2'
        self.LIBSASS_STYLE = 'compressed'


CONFIGS = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
