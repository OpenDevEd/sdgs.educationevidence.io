import pathlib
import re

from environs import Env
from flask_babelex import gettext as _
from whoosh.fields import STORED

from kerko import codecs, extractors, transformers
from kerko.composer import Composer
from kerko.specs import CollectionFacetSpec, FieldSpec

from .transformers import extra_field_cleaner

env = Env()  # pylint: disable=invalid-name
env.read_env()


class Config():
    app_dir = pathlib.Path(env.str('FLASK_APP')).parent.absolute()

    # Get configuration values from the environment.
    SECRET_KEY = env.str('SECRET_KEY')
    KERKO_ZOTERO_API_KEY = env.str('KERKO_ZOTERO_API_KEY')
    KERKO_ZOTERO_LIBRARY_ID = env.str('KERKO_ZOTERO_LIBRARY_ID')
    KERKO_ZOTERO_LIBRARY_TYPE = env.str('KERKO_ZOTERO_LIBRARY_TYPE')
    KERKO_DATA_DIR = env.str('KERKO_DATA_DIR', str(app_dir / 'data' / 'kerko'))

    # Set other configuration variables.
    LOGGING_HANDLER = 'default'
    EXPLAIN_TEMPLATE_LOADING = False

    LIBSASS_INCLUDES = [
        str(pathlib.Path(__file__).parent.parent / 'static' / 'src' / 'vendor' / 'bootstrap' / 'scss'),
        str(pathlib.Path(__file__).parent.parent / 'static' / 'src' / 'vendor' / '@fortawesome' / 'fontawesome-free' / 'scss'),
    ]

    BABEL_DEFAULT_LOCALE = 'en'
    KERKO_WHOOSH_LANGUAGE = 'en'
    KERKO_ZOTERO_LOCALE = 'en-GB'

    HOME_URL = 'https://opendeved.net'
    HOME_TITLE = _("Open Development & Education")
    # HOME_SUBTITLE = _("...")

    ABOUT_URL = 'https://opendeved.net/about/'
    BLOG_URL = 'https://opendeved.net/'
    JOBS_URL = 'https://opendeved.net/jobs/'
    PROGRAMMES_URL = 'https://opendeved.net/programmes/'

    NAV_TITLE = _("Evidence Library")
    KERKO_TITLE = _("Evidence Library – Open Development & Education")
    KERKO_CSL_STYLE = 'apa'
    KERKO_PRINT_ITEM_LINK = True
    KERKO_PRINT_CITATIONS_LINK = True
    KERKO_TEMPLATE_BASE = 'app/base.html.jinja2'
    KERKO_TEMPLATE_LAYOUT = 'app/layout.html.jinja2'
    KERKO_TEMPLATE_SEARCH = 'app/search.html.jinja2'
    KERKO_TEMPLATE_SEARCH_ITEM = 'app/search-item.html.jinja2'
    KERKO_TEMPLATE_ITEM = 'app/item.html.jinja2'
    KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW = True

    KERKO_COMPOSER = Composer(
        whoosh_language=KERKO_WHOOSH_LANGUAGE,
        exclude_default_facets=['facet_tag', 'facet_link', 'facet_item_type'],
        exclude_default_fields=['data'],
        default_child_include_re='^(_publish|publishPDF)$',
        default_child_exclude_re='',
    )

    # Replace the default 'data' extractor to strip unwanted data from the Extra field.
    KERKO_COMPOSER.add_field(
        FieldSpec(
            key='data',
            field_type=STORED,
            extractor=extractors.TransformerExtractor(
                extractor=extractors.RawDataExtractor(),
                transformers=[extra_field_cleaner]
            ),
            codec=codecs.JSONFieldCodec()
        )
    )

    # Add extractors for the 'alternateId' field.
    KERKO_COMPOSER.fields['alternateId'].extractor.extractors.append(
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

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_featured',
            filter_key='featured',
            title=_('Featured publisher'),
            weight=10,
            collection_key='JUDM2WBF',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_pubtype',
            filter_key='pubtype',
            title=_('Publication type'),
            weight=20,
            collection_key='NEH6ARC4',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_theme',
            filter_key='theme',
            title=_('Theme'),
            weight=30,
            collection_key='QK8NXPKZ',
        )
    )

    # TODO: Audience facet.
    # KERKO_COMPOSER.add_facet(
    #     CollectionFacetSpec(
    #         key='facet_audience',
    #         filter_key='audience',
    #         title=_('Audience'),
    #         weight=40,
    #         collection_key='A2V4QW55',
    #     )
    # )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_location',
            filter_key='location',
            title=_('Location'),
            weight=50,
            collection_key='94GNF2EB',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_references',
            filter_key='ref',
            title=_('Other'),
            weight=60,
            collection_key='Y37ULQ86',
        )
    )


class DevelopmentConfig(Config):
    CONFIG = 'development'
    DEBUG = True
    ASSETS_DEBUG = env.bool('ASSETS_DEBUG', True)  # Don't bundle/minify static assets.
    KERKO_ZOTERO_START = env.int('KERKO_ZOTERO_START', 0)
    KERKO_ZOTERO_END = env.int('KERKO_ZOTERO_END', 0)
    LIBSASS_STYLE = 'expanded'
    LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'DEBUG')


class ProductionConfig(Config):
    CONFIG = 'production'
    DEBUG = False
    ASSETS_DEBUG = env.bool('ASSETS_DEBUG', False)
    ASSETS_AUTO_BUILD = False
    LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'WARNING')
    GOOGLE_ANALYTICS_ID = 'UA-169419325-2'
    LIBSASS_STYLE = 'compressed'


CONFIGS = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
