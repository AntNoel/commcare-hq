from datetime import date

from corehq.apps.userreports.specs import EvaluationContext
from custom.intrahealth.tests.utils import TestDataSourceExpressions
from custom.intrahealth.utils import YEKSI_NAA_REPORTS_VISITE_DE_L_OPERATOUR

VISITE_DE_L_OPERATOUR_DATA_SOURCE = 'visite_de_l_operateur.json'


class TestVisiteDeLOperatour(TestDataSourceExpressions):

    data_source_name = VISITE_DE_L_OPERATOUR_DATA_SOURCE

    def test_visite_de_l_operatour_properties_for_post_test_xmlns(self):
        form = {
            'id': 'form_id',
            'xmlns': YEKSI_NAA_REPORTS_VISITE_DE_L_OPERATOUR,
            'domain': 'test-pna',
            'form': {
                'location_id': 'a025fa0f80c8451aabe5040c9dfc5efe',
                'region_name': 'Dakar',
                'PPS_name': 'PPS 1',
                'site_code': 'dakar_rufisque_pps 1',
                'district_name': 'District Rufisque',
                'real_date': '2018-03-07',
                'pps_is_outstock': 0,
                'nb_products_stockout': 0,
                'count_products_select': 0,
                'supply-point': 'fd79174541fa4f3b9924af69ee3db7ad',
                'pps_total_amt_paid': 0,
                'pps_total_amt_owed': 0,
            }
        }

        user = {
            'id': 'user_id',
            'domain': 'test-pna',
            'location_id': 'test_location_id'
        }

        self.database.mock_docs = {
            'user_id': user
        }

        pps_id = self.get_expression('pps_id', 'string')
        region_name = self.get_expression('region_name', 'string')
        pps_name = self.get_expression('pps_name', 'string')
        site_code = self.get_expression('site_code', 'string')
        district_name = self.get_expression('district_name', 'string')
        real_date = self.get_expression('real_date', 'date')
        pps_is_outstock = self.get_expression('pps_is_outstock', 'string')
        nb_products_stockout = self.get_expression('nb_products_stockout', 'integer')
        count_products_select = self.get_expression('count_products_select', 'integer')
        supply_point = self.get_expression('supply-point', 'string')
        pps_total_amt_paid = self.get_expression('pps_total_amt_paid', 'integer')
        pps_total_amt_owed = self.get_expression('pps_total_amt_owed', 'integer')

        self.assertEqual(pps_id(form, EvaluationContext(form, 0)), 'a025fa0f80c8451aabe5040c9dfc5efe')
        self.assertEqual(region_name(form, EvaluationContext(form, 0)), 'Dakar')
        self.assertEqual(pps_name(form, EvaluationContext(form, 0)), 'PPS 1')
        self.assertEqual(site_code(form, EvaluationContext(form, 0)), 'dakar_rufisque_pps 1')
        self.assertEqual(district_name(form, EvaluationContext(form, 0)), 'District Rufisque')
        self.assertEqual(real_date(form, EvaluationContext(form, 0)), date(2018, 3, 1))
        self.assertEqual(pps_is_outstock(form, EvaluationContext(form, 0)), False)
        self.assertEqual(nb_products_stockout(form, EvaluationContext(form, 0)), 0)
        self.assertEqual(count_products_select(form, EvaluationContext(form, 0)), 0)
        self.assertEqual(supply_point(form, EvaluationContext(form, 0)), 'fd79174541fa4f3b9924af69ee3db7ad')
        self.assertEqual(pps_total_amt_paid(form, EvaluationContext(form, 0)), 0)
        self.assertEqual(pps_total_amt_owed(form, EvaluationContext(form, 0)), 0)
