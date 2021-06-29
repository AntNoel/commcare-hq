from datetime import datetime
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.test.testcases import TransactionTestCase

from corehq.apps.auditcare.models import (
    AccessAudit,
    AuditcareMigrationMeta,
    NavigationEventAudit,
)
from corehq.apps.auditcare.utils.migration import (
    AuditCareMigrationUtil,
    get_formatted_datetime_string,
)

from .data.audicare_migraion import (
    audit_test_docs,
    failed_docs,
    navigation_test_docs,
)
from .testutils import delete_couch_docs, save_couch_doc


class TestAuditcareMigrationUtil(TransactionTestCase):
    util = AuditCareMigrationUtil()
    start_time = datetime(2020, 6, 1)

    @classmethod
    def setUpClass(cls):
        cls.key = get_formatted_datetime_string(datetime.now()) + '_' + get_formatted_datetime_string(datetime.now())
        cache.set(cls.util.start_key, cls.start_time)
        return super().setUpClass()

    def test_get_next_batch_start(self):
        start_time = self.util.get_next_batch_start()
        self.assertEqual(start_time, self.start_time)

    @patch(
        'corehq.apps.auditcare.utils.migration.AuditCareMigrationUtil.get_next_batch_start',
        return_value=start_time
    )
    def test_generate_batches(self, _):
        batches = self.util.generate_batches(2, 'h')
        expected_batches = [
            [datetime(2020, 6, 1), datetime(2020, 6, 1, 1)],
            [datetime(2020, 6, 1, 1), datetime(2020, 6, 1, 2)]
        ]
        self.assertEquals(batches, expected_batches)

        batches = self.util.generate_batches(2, 'd')
        expected_batches = [
            [datetime(2020, 6, 1), datetime(2020, 6, 2)],
            [datetime(2020, 6, 2), datetime(2020, 6, 3)]
        ]
        self.assertEquals(batches, expected_batches)

    def test_log_batch_start(self):
        self.util.log_batch_start(self.key)
        self.util.log_batch_start(self.key)

        expected_log = AuditcareMigrationMeta.objects.filter(key=self.key)

        self.assertEqual(len(expected_log), 1)
        self.assertEqual(expected_log[0].key, self.key)
        expected_log[0].delete()

    def test_set_batch_as_finished(self):
        AuditcareMigrationMeta.objects.create(key=self.key, state=AuditcareMigrationMeta.STARTED)

        self.util.set_batch_as_finished(self.key, 30)

        expected_log = AuditcareMigrationMeta.objects.filter(key=self.key)

        self.assertEqual(expected_log[0].state, AuditcareMigrationMeta.FINISHED)
        expected_log[0].delete()

    def test_set_batch_as_errored(self):
        AuditcareMigrationMeta.objects.create(key=self.key, state=AuditcareMigrationMeta.STARTED)

        self.util.set_batch_as_errored(self.key)
        expected_log = AuditcareMigrationMeta.objects.filter(key=self.key)

        self.assertEqual(expected_log[0].state, AuditcareMigrationMeta.ERRORED)
        expected_log[0].delete()

    def test_get_errored_keys(self):
        start_time = datetime(2020, 6, 20)
        end_time = datetime(2020, 6, 21)
        key = get_formatted_datetime_string(start_time) + '_' + get_formatted_datetime_string(end_time)
        obj = AuditcareMigrationMeta.objects.create(key=key, state=AuditcareMigrationMeta.ERRORED)

        keys = self.util.get_errored_keys(1)
        self.assertEqual([[start_time, end_time]], keys)
        obj.delete()

    @classmethod
    def tearDownClass(cls):
        cache.delete(cls.util.start_key)
        AuditcareMigrationMeta.objects.all().delete()
        return super().tearDownClass()
