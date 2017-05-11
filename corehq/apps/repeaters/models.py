from collections import namedtuple
from datetime import datetime, timedelta
import logging
import urllib
import urlparse
import warnings
from django.utils.translation import ugettext_lazy as _
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from requests.exceptions import Timeout, ConnectionError
from corehq.apps.cachehq.mixins import QuickCachedDocumentMixin
from corehq.apps.locations.models import SQLLocation
from corehq.apps.users.models import CommCareUser
from corehq.form_processor.exceptions import XFormNotFound
from corehq.util.datadog.metrics import REPEATER_ERROR_COUNT
from corehq.util.datadog.gauges import datadog_counter
from corehq.util.quickcache import quickcache

from dimagi.ext.couchdbkit import *
from couchdbkit.exceptions import ResourceNotFound

from casexml.apps.case.xml import V2, LEGAL_VERSIONS
from corehq.apps.receiverwrapper.exceptions import DuplicateFormatException
from corehq.form_processor.interfaces.dbaccessors import FormAccessors, CaseAccessors

from couchforms.const import DEVICE_LOG_XMLNS
from dimagi.utils.decorators.memoized import memoized
from dimagi.utils.parsing import json_format_datetime
from dimagi.utils.mixins import UnicodeMixIn
from dimagi.utils.post import simple_post

from .dbaccessors import (
    get_pending_repeat_record_count,
    get_failure_repeat_record_count,
    get_success_repeat_record_count,
    get_cancelled_repeat_record_count
)
from .const import (
    MAX_RETRY_WAIT,
    MIN_RETRY_WAIT,
    RECORD_FAILURE_STATE,
    RECORD_SUCCESS_STATE,
    RECORD_PENDING_STATE,
    RECORD_CANCELLED_STATE,
    POST_TIMEOUT,
)
from .exceptions import RequestConnectionError
from .utils import get_all_repeater_types


def log_repeater_timeout_in_datadog(domain):
    datadog_counter('commcare.repeaters.timeout', tags=[u'domain:{}'.format(domain)])


DELETED = "-Deleted"

FormatInfo = namedtuple('FormatInfo', 'name label generator_class')


class GeneratorCollection(object):
    """Collection of format_name to Payload Generators for a Repeater class

    args:
        repeater_class: A valid child class of Repeater class
    """

    def __init__(self, repeater_class):
        self.repeater_class = repeater_class
        self.default_format = ''
        self.format_generator_map = {}

    def add_new_format(self, format_name, format_label, generator_class, is_default=False):
        """Adds a new format->generator mapping to the collection

        args:
            format_name: unique name to identify the format
            format_label: label to be displayed to the user
            generator_class: child class of .repeater_generators.BasePayloadGenerator

        kwargs:
            is_default: True if the format_name should be default format

        exceptions:
            raises DuplicateFormatException if format is added with is_default while other
            default exists
            raises DuplicateFormatException if format_name alread exists in the collection
        """
        if is_default and self.default_format:
            raise DuplicateFormatException("A default format already exists for this repeater.")
        elif is_default:
            self.default_format = format_name
        if format_name in self.format_generator_map:
            raise DuplicateFormatException("There is already a Generator with this format name.")

        self.format_generator_map[format_name] = FormatInfo(
            name=format_name,
            label=format_label,
            generator_class=generator_class
        )

    def get_default_format(self):
        """returns default format"""
        return self.default_format

    def get_default_generator(self):
        """returns generator class for the default format"""
        raise self.format_generator_map[self.default_format].generator_class

    def get_all_formats(self, for_domain=None):
        """returns all the formats added to this repeater collection"""
        return [(name, format.label) for name, format in self.format_generator_map.iteritems()
                if not for_domain or format.generator_class.enabled_for_domain(for_domain)]

    def get_generator_by_format(self, format):
        """returns generator class given a format"""
        return self.format_generator_map[format].generator_class


class Repeater(QuickCachedDocumentMixin, Document, UnicodeMixIn):
    """
    Represents the configuration of a repeater. Will specify the URL to forward to and
    other properties of the configuration.
    """
    base_doc = 'Repeater'

    domain = StringProperty()
    url = StringProperty()
    format = StringProperty()

    auth_type = StringProperty(choices=("basic", "digest"), required=False)
    username = StringProperty()
    password = StringProperty()
    friendly_name = _("Data")

    @classmethod
    def get_custom_url(cls, domain):
        return None

    @classmethod
    def available_for_domain(cls, domain):
        """Returns whether this repeater can be used by a particular domain
        """
        return True

    def get_pending_record_count(self):
        return get_pending_repeat_record_count(self.domain, self._id)

    def get_failure_record_count(self):
        return get_failure_repeat_record_count(self.domain, self._id)

    def get_success_record_count(self):
        return get_success_repeat_record_count(self.domain, self._id)

    def get_cancelled_record_count(self):
        return get_cancelled_repeat_record_count(self.domain, self._id)

    def _format_or_default_format(self):
        from corehq.apps.repeaters.repeater_generators import RegisterGenerator
        return self.format or RegisterGenerator.default_format_by_repeater(self.__class__)

    def _get_payload_generator(self, payload_format):
        from corehq.apps.repeaters.repeater_generators import RegisterGenerator
        gen = RegisterGenerator.generator_class_by_repeater_format(self.__class__, payload_format)
        return gen(self)

    @property
    @memoized
    def generator(self):
        return self._get_payload_generator(self._format_or_default_format())

    def payload_doc(self, repeat_record):
        raise NotImplementedError

    def get_payload(self, repeat_record):
        return self.generator.get_payload(repeat_record, self.payload_doc(repeat_record))

    def register(self, payload, next_check=None):
        if not self.allowed_to_forward(payload):
            return

        repeat_record = RepeatRecord(
            repeater_id=self.get_id,
            repeater_type=self.doc_type,
            domain=self.domain,
            next_check=next_check or datetime.utcnow(),
            payload_id=payload.get_id
        )
        repeat_record.save()
        return repeat_record

    def allowed_to_forward(self, payload):
        """
        Return True/False depending on whether the payload meets forawrding criteria or not
        """
        return True

    def clear_caches(self):
        if self.__class__ == Repeater:
            cls = self.get_class_from_doc_type(self.doc_type)
        else:
            cls = self.__class__
        # clear cls.by_domain (i.e. filtered by doc type)
        Repeater.by_domain.clear(cls, self.domain)
        # clear Repeater.by_domain (i.e. not filtered by doc type)
        Repeater.by_domain.clear(Repeater, self.domain)

    @classmethod
    @quickcache(['cls.__name__', 'domain'], timeout=5 * 60, memoize_timeout=10)
    def by_domain(cls, domain):
        key = [domain]
        if cls.__name__ in get_all_repeater_types():
            key.append(cls.__name__)
        elif cls.__name__ == Repeater.__name__:
            # In this case the wrap function delegates to the
            # appropriate sub-repeater types.
            pass
        else:
            # Any repeater type can be posted to the API, and the installed apps
            # determine whether we actually know about it.
            # But if we do not know about it, then may as well return nothing now
            return []

        raw_docs = cls.view('receiverwrapper/repeaters',
            startkey=key,
            endkey=key + [{}],
            include_docs=True,
            reduce=False,
            wrap_doc=False
        )

        return [cls.wrap(repeater_doc['doc']) for repeater_doc in raw_docs
                if cls.get_class_from_doc_type(repeater_doc['doc']['doc_type'])]

    @classmethod
    def wrap(cls, data):
        if cls.__name__ == Repeater.__name__:
            cls_ = cls.get_class_from_doc_type(data['doc_type'])
            if cls_:
                return cls_.wrap(data)
            else:
                raise ResourceNotFound('Unknown repeater type: %s' % data)
        else:
            return super(Repeater, cls).wrap(data)

    @staticmethod
    def get_class_from_doc_type(doc_type):
        doc_type = doc_type.replace(DELETED, '')
        repeater_types = get_all_repeater_types()
        if doc_type in repeater_types:
            return repeater_types[doc_type]
        else:
            return None

    def retire(self):
        if DELETED not in self['doc_type']:
            self['doc_type'] += DELETED
        if DELETED not in self['base_doc']:
            self['base_doc'] += DELETED
        self.save()

    def get_url(self, repeat_record):
        # to be overridden
        return self.url

    def allow_retries(self, response):
        """Whether to requeue the repeater when it fails
        """
        return True

    def get_headers(self, repeat_record):
        # to be overridden
        return self.generator.get_headers()

    def _use_basic_auth(self):
        return self.auth_type == "basic"

    def _use_digest_auth(self):
        return self.auth_type == "digest"

    def get_auth(self):
        if self._use_basic_auth():
            return HTTPBasicAuth(self.username, self.password)
        elif self._use_digest_auth():
            return HTTPDigestAuth(self.username, self.password)
        return None

    def fire_for_record(self, repeat_record):
        headers = self.get_headers(repeat_record)
        auth = self.get_auth()
        payload = self.get_payload(repeat_record)
        url = self.get_url(repeat_record)

        try:
            response = simple_post(payload, url, headers=headers, timeout=POST_TIMEOUT, auth=auth)
        except (Timeout, ConnectionError) as error:
            log_repeater_timeout_in_datadog(self.domain)
            return self.handle_response(RequestConnectionError(error), repeat_record)
        except Exception as e:
            return self.handle_response(e, repeat_record)
        else:
            return self.handle_response(response, repeat_record)

    def handle_response(self, result, repeat_record):
        """
        route the result to the success, failure, or exception handlers

        result may be either a response object or an exception
        """
        if isinstance(result, Exception):
            attempt = repeat_record.handle_exception(result)
            self.generator.handle_exception(result, repeat_record)
        elif 200 <= result.status_code < 300:
            attempt = repeat_record.handle_success(result)
            self.generator.handle_success(result, self.payload_doc(repeat_record), repeat_record)
        else:
            attempt = repeat_record.handle_failure(result)
            self.generator.handle_failure(result, self.payload_doc(repeat_record), repeat_record)
        return attempt


class FormRepeater(Repeater):
    """
    Record that forms should be repeated to a new url

    """

    include_app_id_param = BooleanProperty(default=True)
    white_listed_form_xmlns = StringListProperty(default=[])  # empty value means all form xmlns are accepted
    friendly_name = _("Forward Forms")

    @memoized
    def payload_doc(self, repeat_record):
        return FormAccessors(repeat_record.domain).get_form(repeat_record.payload_id)

    def allowed_to_forward(self, payload):
        return (
            payload.xmlns != DEVICE_LOG_XMLNS and
            (not self.white_listed_form_xmlns or payload.xmlns in self.white_listed_form_xmlns)
        )

    def get_url(self, repeat_record):
        url = super(FormRepeater, self).get_url(repeat_record)
        if not self.include_app_id_param:
            return url
        else:
            # adapted from http://stackoverflow.com/a/2506477/10840
            url_parts = list(urlparse.urlparse(url))
            query = urlparse.parse_qsl(url_parts[4])
            try:
                query.append(("app_id", self.payload_doc(repeat_record).app_id))
            except (XFormNotFound, ResourceNotFound):
                return None
            url_parts[4] = urllib.urlencode(query)
            return urlparse.urlunparse(url_parts)

    def get_headers(self, repeat_record):
        headers = super(FormRepeater, self).get_headers(repeat_record)
        headers.update({
            "received-on": self.payload_doc(repeat_record).received_on.isoformat()+"Z"
        })
        return headers

    def __unicode__(self):
        return "forwarding forms to: %s" % self.url


class CaseRepeater(Repeater):
    """
    Record that cases should be repeated to a new url

    """

    version = StringProperty(default=V2, choices=LEGAL_VERSIONS)
    white_listed_case_types = StringListProperty(default=[])  # empty value means all case-types are accepted
    black_listed_users = StringListProperty(default=[])  # users who caseblock submissions should be ignored
    friendly_name = _("Forward Cases")

    def allowed_to_forward(self, payload):
        return self._allowed_case_type(payload) and self._allowed_user(payload)

    def _allowed_case_type(self, payload):
        return not self.white_listed_case_types or payload.type in self.white_listed_case_types

    def _allowed_user(self, payload):
        return self.payload_user_id(payload) not in self.black_listed_users

    def payload_user_id(self, payload):
        # get the user_id who submitted the payload, note, it's not the owner_id
        return payload.actions[-1].user_id

    @memoized
    def payload_doc(self, repeat_record):
        return CaseAccessors(repeat_record.domain).get_case(repeat_record.payload_id)

    def get_headers(self, repeat_record):
        headers = super(CaseRepeater, self).get_headers(repeat_record)
        headers.update({
            "server-modified-on": self.payload_doc(repeat_record).server_modified_on.isoformat()+"Z"
        })
        return headers

    def __unicode__(self):
        return "forwarding cases to: %s" % self.url


class ShortFormRepeater(Repeater):
    """
    Record that form id & case ids should be repeated to a new url

    """

    version = StringProperty(default=V2, choices=LEGAL_VERSIONS)
    friendly_name = _("Forward Form Stubs")

    @memoized
    def payload_doc(self, repeat_record):
        return FormAccessors(repeat_record.domain).get_form(repeat_record.payload_id)

    def allowed_to_forward(self, payload):
        return payload.xmlns != DEVICE_LOG_XMLNS

    def get_headers(self, repeat_record):
        headers = super(ShortFormRepeater, self).get_headers(repeat_record)
        headers.update({
            "received-on": self.payload_doc(repeat_record).received_on.isoformat()+"Z"
        })
        return headers

    def __unicode__(self):
        return "forwarding short form to: %s" % self.url


class AppStructureRepeater(Repeater):
    friendly_name = _("Forward App Schema Changes")

    def payload_doc(self, repeat_record):
        return None


class UserRepeater(Repeater):
    friendly_name = _("Forward Users")

    class Meta(object):
        app_label = 'repeaters'

    @memoized
    def payload_doc(self, repeat_record):
        return CommCareUser.get(repeat_record.payload_id)

    def __unicode__(self):
        return "forwarding users to: %s" % self.url


class LocationRepeater(Repeater):
    friendly_name = _("Forward Locations")

    class Meta(object):
        app_label = 'repeaters'

    @memoized
    def payload_doc(self, repeat_record):
        return SQLLocation.objects.get(location_id=repeat_record.payload_id)

    def __unicode__(self):
        return "forwarding locations to: %s" % self.url


class RepeatRecordAttempt(DocumentSchema):
    cancelled = BooleanProperty(default=False)
    datetime = DateTimeProperty()
    failure_reason = StringProperty()
    next_check = DateTimeProperty()
    succeeded = BooleanProperty(default=False)


class RepeatRecord(Document):
    """
    An record of a particular instance of something that needs to be forwarded
    with a link to the proper repeater object
    """
    overall_tries = IntegerProperty(default=0)
    max_possible_tries = IntegerProperty(default=3)

    repeater_id = StringProperty()
    repeater_type = StringProperty()
    domain = StringProperty()

    last_checked = DateTimeProperty()
    next_check = DateTimeProperty()
    succeeded = BooleanProperty(default=False)
    failure_reason = StringProperty()
    cancelled = BooleanProperty(default=False)

    payload_id = StringProperty()

    @property
    @memoized
    def repeater(self):
        return Repeater.get(self.repeater_id)

    @property
    def url(self):
        warnings.warn("RepeatRecord.url is deprecated. Use Repeater.get_url instead", DeprecationWarning)
        return self.repeater.get_url(self)

    @property
    def state(self):
        state = RECORD_PENDING_STATE
        if self.succeeded:
            state = RECORD_SUCCESS_STATE
        elif self.cancelled:
            state = RECORD_CANCELLED_STATE
        elif self.failure_reason:
            state = RECORD_FAILURE_STATE
        return state

    @classmethod
    def all(cls, domain=None, due_before=None, limit=None):
        json_now = json_format_datetime(due_before or datetime.utcnow())
        repeat_records = RepeatRecord.view("receiverwrapper/repeat_records_by_next_check",
            startkey=[domain],
            endkey=[domain, json_now, {}],
            include_docs=True,
            reduce=False,
            limit=limit,
        )
        return repeat_records

    @classmethod
    def count(cls, domain=None):
        results = RepeatRecord.view("receiverwrapper/repeat_records_by_next_check",
            startkey=[domain],
            endkey=[domain, {}],
            reduce=True,
        ).one()
        return results['value'] if results else 0

    def add_attempt(self, attempt):
        self.last_checked = attempt.datetime
        self.next_check = attempt.next_check
        self.succeeded = attempt.succeeded
        self.cancelled = attempt.cancelled
        if attempt.failure_reason is not None:
            self.failure_reason = attempt.failure_reason

    def make_set_next_try_attempt(self, failure_reason):
        # we use an exponential back-off to avoid submitting to bad urls
        # too frequently.
        assert self.succeeded is False
        assert self.next_check is not None
        window = timedelta(minutes=0)
        if self.last_checked:
            window = self.next_check - self.last_checked
            window += (window // 2)  # window *= 1.5
        if window < MIN_RETRY_WAIT:
            window = MIN_RETRY_WAIT
        elif window > MAX_RETRY_WAIT:
            window = MAX_RETRY_WAIT

        now = datetime.utcnow()
        return RepeatRecordAttempt(
            cancelled=False,
            datetime=now,
            failure_reason=failure_reason,
            next_check=now + window,
            succeeded=False,
        )

    def try_now(self):
        # try when we haven't succeeded and either we've
        # never checked, or it's time to check again
        return not self.succeeded

    def get_payload(self):
        return self.repeater.get_payload(self)

    def handle_payload_exception(self, exception):
        self.succeeded = False
        self.failure_reason = unicode(exception)
        self.cancel()
        self.save()

    def fire(self, force_send=False):
        if self.try_now() or force_send:
            self.overall_tries += 1
            try:
                attempt = self.repeater.fire_for_record(self)
            except Exception as e:
                # todo: seems like this just does everything that handle_exception does but not as well.
                # todo:   seems like they could be combined
                self.handle_payload_exception(e)
                raise
            else:
                self.add_attempt(attempt)
                self.save()

    def handle_success(self, response):
        """Do something with the response if the repeater succeeds
        """
        now = datetime.utcnow()
        return RepeatRecordAttempt(
            cancelled=False,
            datetime=now,
            failure_reason=None,
            next_check=None,
            succeeded=True,
        )

    def handle_failure(self, response):
        """Do something with the response if the repeater fails
        """
        return self._make_failure_attempt(
            u'{}: {}. {}'.format(response.status_code, response.reason, getattr(response, 'content', None)),
            response
        )

    def handle_exception(self, exception):
        """handle internal exceptions
        """
        return self._make_failure_attempt(unicode(exception), None)

    def _make_failure_attempt(self, reason, response):
        datadog_counter(REPEATER_ERROR_COUNT, tags=[
            u'domain:{}'.format(self.domain),
            u'status_code:{}'.format(response.status_code if response else None),
            u'repeater_type:{}'.format(self.repeater_type),
        ])

        if self.repeater.allow_retries(response) and self.overall_tries < self.max_possible_tries:
            return self.make_set_next_try_attempt(reason)
        else:
            now = datetime.utcnow()
            return RepeatRecordAttempt(
                cancelled=True,
                datetime=now,
                failure_reason=reason,
                next_check=None,
                succeeded=False,
            )

    def cancel(self):
        self.next_check = None
        self.cancelled = True

    def requeue(self):
        self.cancelled = False
        self.succeeded = False
        self.failure_reason = ''
        self.overall_tries = 0
        self.next_check = datetime.utcnow()


# import signals
# Do not remove this import, its required for the signals code to run even though not explicitly used in this file
from corehq.apps.repeaters import signals
