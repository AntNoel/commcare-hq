from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand

from corehq.apps.change_feed import topics
from corehq.util.couchdb_management import couch_config
from corehq.util.pagination import PaginationEventHandler
from fluff.pillow import get_fluff_pillow_configs
from pillowtop.reindexer.change_providers.couch import CouchDomainDocTypeChangeProvider
from pillowtop.reindexer.reindexer import PillowChangeProviderReindexer
from pillowtop.utils import get_pillow_by_name, get_all_pillow_configs


class ReindexEventHandler(PaginationEventHandler):

    def __init__(self, log_prefix):
        self.log_prefix = log_prefix

    def page_start(self, total_emitted, *args, **kwargs):
        domain, doc_type = kwargs.get('startkey')
        print (u'{} Fetching rows {}-{} from couch: domain="{}" doc_type="{}"'.format(
            self.log_prefix,
            total_emitted,
            total_emitted + kwargs['limit'] - 1,
            domain,
            doc_type
        ))

    def page_end(self, total_emitted, duration, *args, **kwargs):
        print('{} View call took {}'.format(self.log_prefix, duration))


class Command(BaseCommand):
    args = '<pillow_name>'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Usage is ptop_reindexer_fluff %s' % self.args)

        fluff_configs = {config.name: config for config in get_fluff_pillow_configs()}

        pillow_name = args[0]
        if pillow_name not in fluff_configs:
            raise CommandError('Unrecognised fluff pillow: "{}". Options are:\n\t{}'.format(
                pillow_name, '\n\t'.join(fluff_configs)))

        pillow_getter = get_pillow_by_name(pillow_name, instantiate=False)
        pillow = pillow_getter(delete_filtered=True, chunk_size=0)

        if pillow.kafka_topic in (topics.CASE, topics.FORM):
            couch_db = couch_config.get_db(None)
        elif pillow.kafka_topic == topics.COMMCARE_USER:
            couch_db = couch_config.get_db(settings.NEW_USERS_GROUPS_DB)
        else:
            raise CommandError('Reindexer not configured for topic: {}'.format(pillow.kafka_topic))

        change_provider = CouchDomainDocTypeChangeProvider(
            couch_db=couch_db,
            domains=pillow.domains,
            doc_types=[pillow.doc_type],
            event_handler=ReindexEventHandler(pillow_name),
        )

        PillowChangeProviderReindexer(pillow, change_provider).reindex()
