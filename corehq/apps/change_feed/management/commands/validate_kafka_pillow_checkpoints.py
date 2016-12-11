from optparse import make_option
from django.core.management import BaseCommand
from corehq.apps.change_feed.consumer.feed import KafkaChangeFeed
from corehq.apps.change_feed.exceptions import UnavailableKafkaOffset
from corehq.apps.change_feed.topics import validate_offsets
from pillowtop import get_all_pillow_instances


class Command(BaseCommand):
    help = ("Validates that all pillows that use kafka have checkpoints that still exist "
            "in the kafka feed.")

    option_list = (
        make_option('--print-only',
                    action='store_true',
                    dest='print_only',
                    default=False,
                    help="Only print information, don't fail if checkpoints aren't valid."),
    )

    def handle(self, *args, **options):
        print_only = options['print_only']
        validate_checkpoints(print_only)


def validate_checkpoints(print_only):

    for pillow in get_all_pillow_instances():
        if isinstance(pillow.get_change_feed(), KafkaChangeFeed):
            checkpoint_dict = _get_checkpoint_dict(pillow)
            try:
                validate_offsets(checkpoint_dict)
            except UnavailableKafkaOffset as e:
                message = u'Problem with checkpoint for {}: {}'.format(
                    pillow.pillow_id, e
                )
                if print_only:
                    print message
                else:
                    raise Exception(message)


def _get_checkpoint_dict(pillow):
    sequence = pillow.get_last_checkpoint_sequence()
    if isinstance(sequence, dict):
        sequence_dict = sequence
    else:
        try:
            sequence_int = int(sequence)
        except ValueError:
            # assume this is an old/legacy checkpoint
            return {}
        else:
            sequence_dict = {
                pillow.get_change_feed()._get_single_topic_or_fail(): sequence_int
            }
    # filter out 0's since we don't want to check those as they are likely new pillows
    return {
        k: v for k, v in sequence_dict.items() if v > 0
    }
