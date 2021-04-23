import uuid

from django.test.testcases import TestCase

from corehq.apps.app_manager.models import Application, LinkedApplication
from corehq.apps.domain.shortcuts import create_domain
from corehq.apps.fixtures.models import FixtureDataType, FixtureTypeField
from corehq.apps.linked_domain.models import DomainLink
from corehq.apps.linked_domain.view_helpers import (
    build_app_view_models,
    build_fixture_view_models,
    build_keyword_view_models,
    build_report_view_models,
    get_apps,
    get_fixtures,
    get_keywords,
    get_reports,
)
from corehq.apps.sms.models import Keyword
from corehq.apps.userreports.dbaccessors import delete_all_report_configs
from corehq.apps.userreports.models import (
    DataSourceConfiguration,
    ReportConfiguration,
    ReportMeta,
)


def _create_report(domain, upstream_id=None):
    data_source = DataSourceConfiguration(
        domain=domain,
        table_id=uuid.uuid4().hex,
        referenced_doc_type='XFormInstance',
    )
    data_source.save()
    report = ReportConfiguration(
        domain=domain,
        config_id=data_source._id,
        title='report',
        report_meta=ReportMeta(created_by_builder=True, master_id=upstream_id),
    )
    report.save()

    return report


def _create_keyword(domain, upstream_id=None):
    keyword = Keyword(
        domain=domain,
        keyword="ping",
        description="The description",
        override_open_sessions=True,
        upstream_id=upstream_id
    )
    keyword.save()

    return keyword


def _create_fixture(domain):
    data_type = FixtureDataType(
        domain=domain,
        tag="table",
        fields=[
            FixtureTypeField(
                field_name="fixture_property",
                properties=["test"]
            )
        ],
        item_attributes=[],
        is_global=True
    )
    data_type.save()

    return data_type


class TestBuildViewModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestBuildViewModels, cls).setUpClass()
        cls.domain_obj = create_domain('test-create-view-model-domain')
        cls.domain = cls.domain_obj.name

    @classmethod
    def tearDownClass(cls):
        cls.domain_obj.delete()
        super(TestBuildViewModels, cls).tearDownClass()

    def test_build_app_view_models(self):
        app = Application.new_app(self.domain, "Test Application")
        app.save()
        self.addCleanup(app.delete)
        expected_view_models = [
            {
                'type': 'app',
                'name': 'Application (Test Application)',
                'detail': {'app_id': f'{app._id}'},
                'last_update': None,
                'can_update': True
            }
        ]

        view_models = build_app_view_models({app._id: app})

        self.assertEqual(expected_view_models, view_models)

    def test_build_app_view_models_when_empty(self):
        upstream_apps = {}
        expected_view_models = []

        view_models = build_app_view_models(upstream_apps)

        self.assertEqual(expected_view_models, view_models)

    def test_build_fixture_view_models(self):
        fixture = _create_fixture(self.domain)
        self.addCleanup(fixture.delete)
        expected_view_models = [
            {
                'type': 'fixture',
                'name': f'Lookup Table ({fixture.tag})',
                'detail': {'tag': f'{fixture.tag}'},
                'last_update': None,
                'can_update': True
            }
        ]

        view_models = build_fixture_view_models({fixture._id: fixture})

        self.assertEqual(expected_view_models, view_models)

    def test_build_fixture_view_models_when_empty(self):
        fixtures = {}
        expected_view_models = []

        view_models = build_fixture_view_models(fixtures)

        self.assertEqual(expected_view_models, view_models)

    def test_build_report_view_models(self):
        report = _create_report(self.domain)
        self.addCleanup(report.delete)
        expected_view_models = [
            {
                'type': 'report',
                'name': f'Report ({report.title})',
                'detail': {'report_id': f'{report._id}'},
                'last_update': None,
                'can_update': True
            }
        ]

        view_models = build_report_view_models({report._id: report})

        self.assertEqual(expected_view_models, view_models)

    def test_build_report_view_models_when_empty(self):
        reports = {}
        expected_view_models = []

        view_models = build_report_view_models(reports)

        self.assertEqual(expected_view_models, view_models)

    def test_build_keyword_view_models_original(self):
        keyword = _create_keyword(self.domain)
        self.addCleanup(keyword.delete)

        expected_view_models = [
            {
                'type': 'keyword',
                'name': f'Keyword ({keyword.keyword})',
                'detail': {'keyword_id': f'{keyword.id}', 'linked_keyword_id': None},
                'last_update': None,
                'can_update': True
            }
        ]

        view_models = build_keyword_view_models({keyword.id: keyword})

        self.assertEqual(expected_view_models, view_models)

    def test_build_keyword_view_models_when_empty(self):
        keywords = {}
        expected_view_models = []

        view_models = build_keyword_view_models(keywords)

        self.assertEqual(expected_view_models, view_models)


class TestGetDataModels(TestCase):
    file_path = ('data',)

    @classmethod
    def setUpClass(cls):
        super(TestGetDataModels, cls).setUpClass()
        cls.upstream_domain_obj = create_domain('upstream-domain')
        cls.upstream_domain = cls.upstream_domain_obj.name
        cls.downstream_domain_obj = create_domain('downstream-domain')
        cls.downstream_domain = cls.downstream_domain_obj.name

        cls.original_app = Application.new_app(cls.upstream_domain, "Original Application")
        cls.original_app.linked_whitelist = [cls.downstream_domain]
        cls.original_app.save()

        cls.linked_app = LinkedApplication.new_app(cls.downstream_domain, "Linked Application")
        cls.linked_app.upstream_app_id = cls.original_app._id
        cls.linked_app.save()

        cls.original_report = _create_report(cls.upstream_domain)
        cls.linked_report = _create_report(cls.downstream_domain, upstream_id=cls.original_report._id)

        cls.original_keyword = _create_keyword(cls.upstream_domain)
        cls.linked_keyword = _create_keyword(cls.downstream_domain, upstream_id=cls.original_keyword.id)

        cls.original_fixture = _create_fixture(cls.upstream_domain)

        cls.domain_link = DomainLink.link_domains(cls.downstream_domain, cls.upstream_domain)

    @classmethod
    def tearDownClass(cls):
        delete_all_report_configs()
        cls.original_fixture.delete()
        cls.original_keyword.delete()
        cls.linked_keyword.delete()
        cls.original_report.delete()
        cls.linked_report.delete()
        cls.linked_app.delete()
        cls.original_app.delete()
        cls.domain_link.delete()
        cls.upstream_domain_obj.delete()
        cls.downstream_domain_obj.delete()
        super(TestGetDataModels, cls).tearDownClass()

    def test_get_apps_for_upstream_domain(self):
        expected_upstream_app_names = [self.original_app._id]
        expected_downstream_app_names = []

        upstream_apps, downstream_apps = get_apps(self.upstream_domain)
        actual_upstream_app_names = [app._id for app in upstream_apps.values()]
        actual_downstream_app_names = [app._id for app in downstream_apps.values()]

        self.assertEqual(expected_upstream_app_names, actual_upstream_app_names)
        self.assertEqual(expected_downstream_app_names, actual_downstream_app_names)

    def test_get_apps_for_downstream_domain(self):
        expected_original_app_names = []
        expected_linked_app_names = [self.linked_app._id]

        original_apps, linked_apps = get_apps(self.downstream_domain)
        actual_original_app_names = [app._id for app in original_apps.values()]
        actual_linked_app_names = [app._id for app in linked_apps.values()]

        self.assertEqual(expected_original_app_names, actual_original_app_names)
        self.assertEqual(expected_linked_app_names, actual_linked_app_names)

    def test_get_reports_for_upstream_domain(self):
        expected_original_reports = [self.original_report._id]
        expected_linked_reports = []

        original_reports, linked_reports = get_reports(self.upstream_domain)
        actual_original_reports = [report._id for report in original_reports.values()]
        actual_linked_reports = [report._id for report in linked_reports.values()]

        self.assertEqual(expected_original_reports, actual_original_reports)
        self.assertEqual(expected_linked_reports, actual_linked_reports)

    def test_get_reports_for_downstream_domain(self):
        expected_original_reports = []
        expected_linked_reports = [self.linked_report._id]

        original_reports, linked_reports = get_reports(self.downstream_domain)
        actual_original_reports = [report._id for report in original_reports.values()]
        actual_linked_reports = [report._id for report in linked_reports.values()]

        self.assertEqual(expected_original_reports, actual_original_reports)
        self.assertEqual(expected_linked_reports, actual_linked_reports)

    def test_get_keywords_for_upstream_domain(self):
        expected_original_keywords = [str(self.original_keyword.id)]
        expected_linked_keywords = []

        original_keywords, linked_keywords = get_keywords(self.upstream_domain)
        actual_original_keywords = [str(keyword.id) for keyword in original_keywords.values()]
        actual_linked_keywords = [str(keyword.id) for keyword in linked_keywords.values()]

        self.assertEqual(expected_original_keywords, actual_original_keywords)
        self.assertEqual(expected_linked_keywords, actual_linked_keywords)

    def test_get_keywords_for_downstream_domain(self):
        expected_original_keywords = []
        expected_linked_keywords = [str(self.linked_keyword.id)]

        original_keywords, linked_keywords = get_keywords(self.downstream_domain)
        actual_original_keywords = [str(keyword.id) for keyword in original_keywords.values()]
        actual_linked_keywords = [str(keyword.id) for keyword in linked_keywords.values()]

        self.assertEqual(expected_original_keywords, actual_original_keywords)
        self.assertEqual(expected_linked_keywords, actual_linked_keywords)

    def test_get_fixtures_for_upstream_domain(self):
        expected_original_fixtures = [self.original_fixture._id]
        expected_linked_fixtures = []

        original_fixtures, linked_fixtures = get_fixtures(self.upstream_domain, None)
        actual_original_fixtures = [fixture._id for fixture in original_fixtures.values()]
        actual_linked_fixtures = [fixture._id for fixture in linked_fixtures.values()]

        self.assertEqual(expected_original_fixtures, actual_original_fixtures)
        self.assertEqual(expected_linked_fixtures, actual_linked_fixtures)

    def test_get_fixtures_for_downstream_domain(self):
        expected_original_fixtures = []
        expected_linked_fixtures = [self.original_fixture._id]

        original_fixtures, linked_fixtures = get_fixtures(self.downstream_domain, self.domain_link)
        actual_original_fixtures = [fixture._id for fixture in original_fixtures.values()]
        actual_linked_fixtures = [fixture._id for fixture in linked_fixtures.values()]

        self.assertEqual(expected_original_fixtures, actual_original_fixtures)
        self.assertEqual(expected_linked_fixtures, actual_linked_fixtures)
