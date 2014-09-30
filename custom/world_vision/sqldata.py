from sqlagg import CountUniqueColumn, BaseColumn
from sqlagg.columns import SimpleColumn, SumColumn
from sqlagg.filters import IN
from sqlagg.filters import LT, LTE, AND, GTE, GT, EQ, NOTEQ, OR, BETWEEN
from sqlalchemy import func, cast, Numeric
from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from corehq.apps.reports.sqlreport import SqlData, DatabaseColumn, DataFormatter, TableDataFormat, calculate_total_row
from custom.world_vision.custom_queries import CustomMedianColumn

LOCATION_HIERARCHY = {
    "lvl_1": {
        "prop": "lvl_1",
        "name": "State"
    },
    "lvl_2": {
        "prop": "lvl_2",
        "name": "District"
    },
    "lvl_3": {
        "prop": "lvl_3",
        "name": "Block"
    },
    "lvl_4": {
        "prop": "lvl_4",
        "name": "PHC"
    }
}


class BaseSqlData(SqlData):
    show_total = False
    datatables = False
    show_charts = False
    no_value = {'sort_key': 0, 'html': 0}
    fix_left_col = False
    total_row_name = "Total"
    custom_total_calculate = False

    def percent_fn(self, x, y):
        return "%.2f%%" % (100 * float(y or 0) / (x or 1))

    @property
    def filters(self):
        filters = [BETWEEN("date", "startdate", "enddate")]
        for k, v in LOCATION_HIERARCHY.iteritems():
            if v['prop'] in self.config and self.config[v['prop']]:
                filters.append(IN(k, v['prop']))
        return filters

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def group_by(self):
        return []

    @property
    def rows(self):
        formatter = DataFormatter(TableDataFormat(self.columns, no_value=self.no_value))
        return list(formatter.format(self.data, keys=self.keys, group_by=self.group_by))

    @property
    def data(self):
        return super(BaseSqlData, self).data

    def _get_rows(self, dict, rows):
        total_row = calculate_total_row(rows)
        total = total_row[-1] if total_row else 0
        result = []
        for (k, v) in dict.iteritems():
            number = [row[1]['html'] for row in rows if row[0] == k]
            number = number[0] if number else 0
            result.append([{'sort_key':v, 'html': v}, {'sort_key':number, 'html': number},
                   {'sort_key':self.percent_fn(total, number), 'html': self.percent_fn(total, number)}
            ])
        return result

class LocationSqlData(SqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    geography_config = LOCATION_HIERARCHY

    @property
    def filters(self):
        return [EQ('domain', 'domain')]

    @property
    def filter_values(self):
        return {'domain': 'wvindia2'}

    @property
    def group_by(self):
        return [k for k in self.geography_config.keys()]

    @property
    def columns(self):
        levels = [k for k in self.geography_config.keys()]
        columns = []
        for k in levels:
            columns.append(DatabaseColumn(k, SimpleColumn(k)))
        return columns


class MotherRegistrationOverview(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'mother_registration_overview'
    title = 'Mother Registration Overview'

    @property
    def filters(self):
        #TODO: if date_not_selected:
        if False:
            return super(MotherRegistrationOverview, self).filters[1:]
        else:
            return super(MotherRegistrationOverview, self).filters

    @property
    def rows(self):
        result = []
        for column in self.columns:
            result.append([{'sort_key': column.header, 'html': column.header},
                           {'sort_key': self.data[column.slug], 'html': self.data[column.slug]}])
        return result

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number')])

    @property
    def columns(self):
        columns = [
            DatabaseColumn("Total mothers registered ever",
                CountUniqueColumn('doc_id',
                    alias="total",
                    filters=[NOTEQ('doc_id', 'empty')]
                )
            ),
        ]
        #TODO: if date_not_selected:
        if False:
            columns.extend([
                DatabaseColumn("Total open mother cases",
                    CountUniqueColumn('doc_id',
                        alias="opened",
                        filters=self.filters + [EQ('closed_on', 'empty')]
                    )
                ),
                DatabaseColumn("Total closed mother cases",
                    CountUniqueColumn('doc_id',
                        alias="closed",
                        filters=self.filters +  [NOTEQ('closed_on', 'empty')]
                    )
                ),
                DatabaseColumn("New registrations during last 30 days",
                        CountUniqueColumn('doc_id',
                            alias="new_registrations",
                            filters=self.filters + [AND([LTE('opened_on', "last_month"), GTE('opened_on', "today")])]
                        )
                )
            ])
        else:
            columns.extend([
                DatabaseColumn("Mother cases open at end of time period",
                    CountUniqueColumn('doc_id',
                        alias="opened",
                        filters=self.filters + [AND([LTE('opened_on', "stred"), OR([EQ('closed_on', 'empty'), GT('closed_on', "stred")])])]
                    )
                ),
                DatabaseColumn("Mother cases closed during the time period",
                    CountUniqueColumn('doc_id',
                        alias="closed",
                        filters=self.filters + [AND([NOTEQ('closed_on', 'empty'), LTE('opened_on', "stred"), LTE('closed_on', "stred")])]
                    )
                ),
                DatabaseColumn("Total mothers followed during the time period",
                    CountUniqueColumn('doc_id',
                        alias="followed",
                        filters=self.filters + [AND([LTE('opened_on', "stred"), OR([EQ('closed_on', 'empty'), GTE('closed_on', "strsd")])])]
                    )
                ),
                DatabaseColumn("New registrations during time period",
                    CountUniqueColumn('doc_id',
                        alias="new_registrations",
                        filters=self.filters + [AND([LTE('opened_on', "stred"), GTE('opened_on', "strsd")])]
                    )
                )
            ])
        return columns


class ClosedMotherCasesBreakdown(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'closed_mother_cases-breakdown'
    title = 'Closed Mother Cases Breakdown'
    show_total = True
    total_row_name = "Mother cases closed during the time period"
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def group_by(self):
        return ['reason_for_mother_closure']

    @property
    def rows(self):
        rows = super(ClosedMotherCasesBreakdown, self).rows
        total_row = calculate_total_row(rows)
        total = total_row[-1] if total_row else 0
        for row in rows:
            from custom.world_vision import REASON_FOR_CLOSURE_MAPPING
            row[0] = REASON_FOR_CLOSURE_MAPPING[row[0]]
            percent = self.percent_fn(total, row[1]['html'])
            row.append({'sort_key':percent, 'html': percent})
        return rows

    @property
    def filters(self):
        filter = super(ClosedMotherCasesBreakdown, self).filters
        filter.append(NOTEQ('reason_for_mother_closure', 'empty'))
        return filter

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Reason for closure'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Reason for closure", SimpleColumn('reason_for_mother_closure')),
            DatabaseColumn("Number", CountUniqueColumn('doc_id'))
        ]


class PregnantMotherBreakdownByTrimester(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'pregnant_mother_by_trimester'
    title = 'Pregnant Woman Breakdown by Trimester'
    show_total = True
    total_row_name = "Total pregnant "
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''


    def percent_fn(self, y):
        x = self.data['trimester_1'] + self.data['trimester_2'] + self.data['trimester_3']
        return "%(p).2f%%" % \
            {
                "p": (100 * int(y or 0) / (x or 1))
            }

    @property
    def filters(self):
        filter = super(PregnantMotherBreakdownByTrimester, self).filters
        filter.append(EQ('mother_state', 'pregnant_mother_type'))
        return filter

    @property
    def rows(self):
        result = []
        for column in self.columns:
            percent = self.percent_fn(self.data[column.slug])
            result.append([{'sort_key': column.header, 'html': column.header},
                           {'sort_key': self.data[column.slug], 'html': self.data[column.slug]},
                           {'sort_key': 'percentage', 'html': percent}]
            )
        return result

    @property
    def columns(self):
        return [
            DatabaseColumn("Trimester 1",
                CountUniqueColumn('doc_id',
                    alias="trimester_1",
                    filters=self.filters + [AND([LTE('lmp', "today"), GTE('lmp', "first_trimester_start_date"), NOTEQ('lmp', 'empty')])]
                )
            ),
            DatabaseColumn("Trimester 2",
                CountUniqueColumn('doc_id',
                    alias="trimester_2",
                    filters=self.filters + [AND([LTE('lmp', "second_trimester_start_date"), GTE('lmp', "second_trimester_end_date"), NOTEQ('lmp', 'empty')])]
                )
            ),
            DatabaseColumn("Trimester 3",
                CountUniqueColumn('doc_id',
                    alias="trimester_3",
                    filters=self.filters + [AND([LTE('lmp', 'third_trimester_start_date'), NOTEQ('lmp', 'empty')])]
                )
            )
        ]


class AnteNatalCareServiceOverview(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'ante_natal_care_service_overview'
    title = 'Ante Natal Care Service Overview'

    @property
    def filters(self):
        filter = super(AnteNatalCareServiceOverview, self).filters
        filter.append(EQ('mother_state', 'pregnant_mother_type'))
        return filter

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number'),
                                  DataTablesColumn('Total Eligible'), DataTablesColumn('Percentage')])

    @property
    def rows(self):
        result = [[{'sort_key': self.columns[0].header, 'html': self.columns[0].header},
                  {'sort_key': self.data[self.columns[0].slug], 'html': self.data[self.columns[0].slug]},
                  {'sort_key': 'n/a', 'html': 'n/a'},
                  {'sort_key': 'n/a', 'html': 'n/a'}]]
        for i in range(1,5):
            result.append([{'sort_key': self.columns[i].header, 'html': self.columns[i].header},
                           {'sort_key': self.data[self.columns[i].slug], 'html': self.data[self.columns[i].slug]},
                           {'sort_key': self.data[self.columns[i + 4].slug], 'html': self.data[self.columns[i + 4].slug]},
                           {'sort_key': self.percent_fn(self.data[self.columns[i + 4].slug], self.data[self.columns[i].slug]),
                            'html': self.percent_fn(self.data[self.columns[i + 4].slug], self.data[self.columns[i].slug])}])
        return result

    @property
    def columns(self):
        return [

            DatabaseColumn("Total pregnant",
                CountUniqueColumn('doc_id', alias="total_pregnant"),
            ),
            DatabaseColumn("ANC3",
                CountUniqueColumn('doc_id', alias="anc_3", filters=self.filters + [EQ('anc_3', 'yes')]),
            ),
            DatabaseColumn("TT Completed (TT2 or Booster)",
                CountUniqueColumn('doc_id', alias="tt_completed",
                                  filters=self.filters + [OR([EQ('tt_2', 'yes'), EQ('tt_booster', 'yes')])]),
            ),
            DatabaseColumn("Taking IFA tablets",
                CountUniqueColumn('doc_id', alias="ifa_tablets", filters=self.filters + [EQ('iron_folic', 'yes')]),
            ),
            DatabaseColumn("Completed 100 IFA tablets",
                CountUniqueColumn('doc_id', alias="100_tablets", filters=self.filters + [EQ('completed_100_ifa', 'yes')]),
            ),
            DatabaseColumn("ANC3 Total Eligible",
                CountUniqueColumn('doc_id', alias="anc_3_eligible",
                                  filters=self.filters + [AND([EQ('anc_2', 'yes'), LTE('lmp', 'days_224')])]),
            ),
            DatabaseColumn("TT Completed (TT2 or Booster) Total Eligible",
                CountUniqueColumn('doc_id', alias="tt_completed_eligible",
                                  filters=self.filters + [OR([EQ('tt_1', 'yes'), EQ('previous_tetanus', 'yes')])]),
            ),
            DatabaseColumn("Taking IFA tablets Total Eligible",
                CountUniqueColumn('doc_id', alias="ifa_tablets_eligible"),
            ),
            DatabaseColumn("Completed 100 IFA tablets Total Eligible",
                CountUniqueColumn('doc_id', alias="100_tablets_eligible", filters=self.filters + [LTE('lmp', 'days_195')]),
            )
        ]

class AnteNatalCareServiceOverviewExtended(AnteNatalCareServiceOverview):
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def rows(self):
        result = [[{'sort_key': self.columns[0].header, 'html': self.columns[0].header},
                  {'sort_key': self.data[self.columns[0].slug], 'html': self.data[self.columns[0].slug]},
                  {'sort_key': 'n/a', 'html': 'n/a'},
                  {'sort_key': 'n/a', 'html': 'n/a'}]]
        for i in range(1,15):
            result.append([{'sort_key': self.columns[i].header, 'html': self.columns[i].header},
                           {'sort_key': self.data[self.columns[i].slug], 'html': self.data[self.columns[i].slug]},
                           {'sort_key': self.data[self.columns[i + 14].slug], 'html': self.data[self.columns[i + 14].slug]},
                           {'sort_key': self.percent_fn(self.data[self.columns[i + 14].slug], self.data[self.columns[i].slug]),
                            'html': self.percent_fn(self.data[self.columns[i + 14].slug], self.data[self.columns[i].slug])}])
        return result

    @property
    def columns(self):
        return [
            DatabaseColumn("Total pregnant",
                CountUniqueColumn('doc_id', alias="total_pregnant"),
            ),
            DatabaseColumn("No ANC",
                CountUniqueColumn('doc_id', alias="no_anc", filters=self.filters + [NOTEQ('anc_1', 'yes')]),
            ),
            DatabaseColumn("ANC1",
                CountUniqueColumn('doc_id', alias="anc_1", filters=self.filters + [EQ('anc_1', 'yes')]),
            ),
            DatabaseColumn("ANC2",
                CountUniqueColumn('doc_id', alias="anc_2", filters=self.filters + [EQ('anc_2', 'yes')]),
            ),
            DatabaseColumn("ANC3",
                CountUniqueColumn('doc_id', alias="anc_3", filters=self.filters + [EQ('anc_3', 'yes')]),
            ),
            DatabaseColumn("ANC4",
                CountUniqueColumn('doc_id', alias="anc_4", filters=self.filters + [EQ('anc_4', 'yes')]),
            ),
            DatabaseColumn("TT1",
                CountUniqueColumn('doc_id', alias="tt_1", filters=self.filters + [EQ('tt_1', 'yes')]),
            ),
            DatabaseColumn("TT2",
                CountUniqueColumn('doc_id', alias="tt_2", filters=self.filters + [EQ('tt_2', 'yes')]),
            ),
            DatabaseColumn("TT Booster",
                CountUniqueColumn('doc_id', alias="tt_booster", filters=self.filters + [EQ('tt_booster', 'yes')]),
            ),
            DatabaseColumn("TT Completed (TT2 or Booster)",
                CountUniqueColumn('doc_id', alias="tt_completed",
                                  filters=self.filters + [OR([EQ('tt_2', 'yes'), EQ('tt_booster', 'yes')])]),
            ),
            DatabaseColumn("IFA tablets",
                CountUniqueColumn('doc_id', alias="ifa_tablets", filters=self.filters + [EQ('iron_folic', 'yes')]),
            ),
            DatabaseColumn("Completed 100 IFA tablets",
                CountUniqueColumn('doc_id', alias="100_tablets", filters=self.filters + [EQ('completed_100_ifa', 'yes')]),
            ),
            DatabaseColumn("Clinically anemic mothers",
                CountUniqueColumn('doc_id', alias="clinically_anemic", filters=self.filters + [EQ('anemia_signs', 'yes')]),
            ),
            DatabaseColumn("Number of pregnant mother referrals due to danger signs",
                CountUniqueColumn('doc_id', alias="danger_signs", filters=self.filters + [EQ('currently_referred', 'yes')]),
            ),
            DatabaseColumn("Knows closest health facility",
                CountUniqueColumn('doc_id', alias="knows_closest_facility", filters=self.filters + [EQ('knows_closest_facility', 'yes')]),
            ),
            DatabaseColumn("No ANC Total Eligible",
                CountUniqueColumn('doc_id', alias="no_anc_eligible", filters=self.filters + [LTE('lmp', 'days_84')]),
            ),
            DatabaseColumn("ANC1 Total Eligible",
                CountUniqueColumn('doc_id', alias="anc_1_eligible", filters=self.filters + [LTE('lmp', 'days_84')]),
            ),
            DatabaseColumn("ANC2 Total Eligible",
                CountUniqueColumn('doc_id', alias="anc_2_eligible",
                                  filters=self.filters + [AND([EQ('anc_1', 'yes'), LTE('lmp', 'days_168')])]),
            ),
            DatabaseColumn("ANC3 Total Eligible",
                CountUniqueColumn('doc_id', alias="anc_3_eligible",
                                  filters=self.filters + [AND([EQ('anc_2', 'yes'), LTE('lmp', 'days_224')])]),
            ),
            DatabaseColumn("ANC4 Total Eligible",
                CountUniqueColumn('doc_id', alias="anc_4_eligible",
                                  filters=self.filters + [AND([EQ('anc_3', 'yes'), LTE('lmp', 'days_245')])]),
            ),
            DatabaseColumn("TT1 Total Eligible",
                CountUniqueColumn('doc_id', alias="tt_1_eligible", filters=self.filters + [NOTEQ('previous_tetanus', 'yes')]),
            ),
            DatabaseColumn("TT2 Total Eligible",
                CountUniqueColumn('doc_id', alias="tt_2_eligible", filters=self.filters + [EQ('tt_1', 'yes')]),
            ),
            DatabaseColumn("TT Booster Total Eligible",
                CountUniqueColumn('doc_id', alias="tt_booster_eligible", filters=self.filters + [EQ('previous_tetanus', 'yes')]),
            ),
            DatabaseColumn("TT Completed (TT2 or Booster) Total Eligible",
                CountUniqueColumn('doc_id', alias="tt_completed_eligible",
                                  filters=self.filters + [OR([EQ('tt_1', 'yes'), EQ('previous_tetanus', 'yes')])]),
            ),
            DatabaseColumn("Taking IFA tablets Total Eligible",
                CountUniqueColumn('doc_id', alias="ifa_tablets_eligible"),
            ),
            DatabaseColumn("Completed 100 IFA tablets Total Eligible",
                CountUniqueColumn('doc_id', alias="100_tablets_eligible", filters=self.filters + [LTE('lmp', 'days_195')]),
            ),
            DatabaseColumn("Clinically anemic mothers Total Eligible",
                CountUniqueColumn('doc_id', alias="clinically_anemic_eligible"),
            ),
            DatabaseColumn("Number of mother referrals due to danger signs Total Eligible",
                CountUniqueColumn('doc_id', alias="danger_signs_eligible"),
            ),
            DatabaseColumn("Know closest health facility Total Eligible",
                CountUniqueColumn('doc_id', alias="knows_closest_facility_eligible"),
            )
        ]


class DeliveryPlaceDetails(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'delivery_place_details'
    title = 'Delivery Details'

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def filters(self):
        return super(DeliveryPlaceDetails, self).filters + [NOTEQ('delivery_date', 'empty')]

    @property
    def columns(self):
        return [
            DatabaseColumn("Total Deliveries (with/without outcome)",
                CountUniqueColumn('doc_id', alias="total_delivery", filters=self.filters),
            ),
            DatabaseColumn("Institutional deliveries",
                CountUniqueColumn('doc_id', alias="institutional_deliveries",
                                  filters=self.filters + [OR([EQ('place_of_birth', 'health_center'), EQ('place_of_birth', "hospital")])]
                )
            )
        ]

    @property
    def rows(self):
        result = []
        for idx, column in enumerate(self.columns):
            if idx == 0:
                percent = 'n/a'
            else:
                percent = self.percent_fn(self.data['total_delivery'], self.data[column.slug])

            result.append([{'sort_key': column.header, 'html': column.header},
                           {'sort_key': self.data[column.slug], 'html': self.data[column.slug]},
                           {'sort_key': 'percentage', 'html': percent}]
            )
        return result


class DeliveryLiveBirthDetails(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'delivery_live_birth_details'
    title = ''
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Total live births",
                SumColumn('number_of_children_total', filters=self.filters, alias='total_live_births')
            ),
            DatabaseColumn("Live birth (Male)",
                SumColumn('number_of_boys_total', filters=self.filters)
            ),
            DatabaseColumn("Live birth (Female)",
                SumColumn('number_of_girls_total', filters=self.filters,)
            )
        ]

    @property
    def rows(self):
        result = []
        for idx, column in enumerate(self.columns):
            if idx == 0:
                percent = 'n/a'
            else:
                percent = self.percent_fn(self.data['total_live_births'], self.data[column.slug])

            result.append([{'sort_key': column.header, 'html': column.header},
                           {'sort_key': self.data[column.slug], 'html': self.data[column.slug]},
                           {'sort_key': 'percentage', 'html': percent}]
            )
        return result


class DeliveryStillBirthDetails(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'delivery_still_birth_details'
    title = ''


    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Still births",
                SumColumn('number_of_children_born_dead_total', filters=self.filters)
            ),
            DatabaseColumn("Abortions",
                CountUniqueColumn('doc_id', alias="abortions", filters=self.filters + [EQ('reason_for_mother_closure', 'abortion')]),
            ),
        ]

    @property
    def rows(self):
        result = []
        for column in self.columns:
            result.append([{'sort_key': column.header, 'html': column.header},
                           {'sort_key': self.data[column.slug], 'html': self.data[column.slug]}]
            )
        return result



class PostnatalCareOverview(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'postnatal_care_overview'
    title = 'Postnatal Care Overview'
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number'),
                                  DataTablesColumn('Total Eligible'), DataTablesColumn('Percentage')])

    @property
    def rows(self):
        result = []
        for i in range(0,4):
            result.append([{'sort_key': self.columns[i].header, 'html': self.columns[i].header},
                           {'sort_key': self.data[self.columns[i].slug], 'html': self.data[self.columns[i].slug]},
                           {'sort_key': self.data[self.columns[i + 4].slug], 'html': self.data[self.columns[i + 4].slug]},
                           {'sort_key': self.percent_fn(self.data[self.columns[i + 4].slug], self.data[self.columns[i].slug]),
                            'html': self.percent_fn(self.data[self.columns[i + 4].slug], self.data[self.columns[i].slug])}])
        return result

    @property
    def columns(self):
        return [
            DatabaseColumn("PNC 1 visits",
                CountUniqueColumn('doc_id', alias="pnc_1", filters=self.filters + [EQ('pp_1_done', 'yes')]),
            ),
            DatabaseColumn("PNC 2 visits",
                CountUniqueColumn('doc_id', alias="pnc_2", filters=self.filters + [EQ('pp_2_done', 'yes')]),
            ),
            DatabaseColumn("PNC 3 visits",
                CountUniqueColumn('doc_id', alias="pnc_3", filters=self.filters + [EQ('pp_3_done', 'yes')]),
            ),
            DatabaseColumn("PNC 4 visits",
                CountUniqueColumn('doc_id', alias="pnc_4", filters=self.filters + [EQ('pp_4_done', 'yes')]),
            ),
            DatabaseColumn("PNC 1 visits Total Eligible",
                CountUniqueColumn('doc_id', alias="pnc_1_eligible",
                                  filters=self.filters + [AND([NOTEQ('delivery_date', 'empty'), LTE('delivery_date', 'today')])]),
            ),
            DatabaseColumn("PNC 2 visits Total Eligible",
                CountUniqueColumn('doc_id', alias="pnc_2_eligible",
                                  filters=self.filters + [AND([NOTEQ('delivery_date', 'empty'), LTE('delivery_date', 'days_2')])]),
            ),
            DatabaseColumn("PNC 3 visits Total Eligible",
                CountUniqueColumn('doc_id', alias="pnc_3_eligible",
                                  filters=self.filters + [AND([NOTEQ('delivery_date', 'empty'), LTE('delivery_date', 'days_5')])]),
            ),
            DatabaseColumn("PNC 4 visits Total Eligible",
                CountUniqueColumn('doc_id', alias="pnc_4_eligible",
                                  filters=self.filters + [AND([NOTEQ('delivery_date', 'empty'), LTE('delivery_date', 'days_21')])]),
            )
        ]

class FamilyPlanningMethods(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'family_planning_methods'
    title = 'Family Planning Methods'
    show_total = True
    total_row_name = "Total Families who reported using Family Planning"
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def group_by(self):
        return ['fp_method']

    @property
    def rows(self):
        from custom.world_vision import FAMILY_PLANNING_METHODS
        return self._get_rows(FAMILY_PLANNING_METHODS, super(FamilyPlanningMethods, self).rows)

    @property
    def filters(self):
        filter = super(FamilyPlanningMethods, self).filters
        filter.append(NOTEQ('fp_method', 'empty'))
        return filter

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Method'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Method", SimpleColumn('fp_method')),
            DatabaseColumn("Number", CountUniqueColumn('doc_id'))
        ]

class CauseOfMaternalDeaths(BaseSqlData):
    table_name = "fluff_WorldVisionMotherFluff"
    slug = 'Cause_of_maternal_deaths'
    title = 'Cause of Maternal Deaths'
    show_total = True
    total_row_name = "Total Mother Deaths"
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def group_by(self):
        return ['cause_of_death_maternal']

    @property
    def rows(self):
        from custom.world_vision import MOTHER_DEATH_MAPPING
        return self._get_rows(MOTHER_DEATH_MAPPING, super(CauseOfMaternalDeaths, self).rows)

    @property
    def filters(self):
        filter = super(CauseOfMaternalDeaths, self).filters
        filter.append(EQ('reason_for_mother_closure', 'death'))
        return filter

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Reason'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Reason", SimpleColumn('cause_of_death_maternal')),
            DatabaseColumn("Number", CountUniqueColumn('doc_id'))
        ]

class ChildRegistrationDetails(MotherRegistrationOverview):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'child_registration_overview'
    title = 'Child Registration Details'

    @property
    def columns(self):
        columns = [
            DatabaseColumn("Total children registered ever",
                CountUniqueColumn('doc_id',
                    alias="total",
                    filters=self.filters
                )
            ),
        ]
        #TODO: if date_not_selected:
        if False:
            columns.extend([
                DatabaseColumn("Total open children cases",
                    CountUniqueColumn('doc_id',
                        alias="opened",
                        filters=self.filters + [EQ('closed_on', 'empty')]
                    )
                ),
                DatabaseColumn("Total closed children cases",
                    CountUniqueColumn('doc_id',
                        alias="closed",
                        filters=self.filters +  [NOTEQ('closed_on', 'empty')]
                    )
                ),
                DatabaseColumn("New registrations during last 30 days",
                        CountUniqueColumn('doc_id',
                            alias="new_registrations",
                            filters=self.filters + [AND([LTE('opened_on', "last_month"), GTE('opened_on', "today")])]
                        )
                )
            ])
        else:
            columns.extend([
                DatabaseColumn("Children cases open at end of time period",
                    CountUniqueColumn('doc_id',
                        alias="opened",
                        filters=self.filters + [AND([LTE('opened_on', "stred"), OR([EQ('closed_on', 'empty'), GT('closed_on', "stred")])])]
                    )
                ),
                DatabaseColumn("Children cases closed during the time period",
                    CountUniqueColumn('doc_id',
                        alias="closed",
                        filters=self.filters + [AND([NOTEQ('closed_on', 'empty'), LTE('opened_on', "stred"), LTE('closed_on', "stred")])]
                    )
                ),
                DatabaseColumn("Total children followed during the time period",
                    CountUniqueColumn('doc_id',
                        alias="followed",
                        filters=self.filters + [AND([LTE('opened_on', "stred"), OR([EQ('closed_on', 'empty'), GTE('closed_on', "strsd")])])]
                    )
                ),
                DatabaseColumn("New registrations during time period",
                    CountUniqueColumn('doc_id',
                        alias="new_registrations",
                        filters=self.filters + [AND([LTE('opened_on', "stred"), GTE('opened_on', "strsd")])]
                    )
                )
            ])
        return columns

class ClosedChildCasesBreakdown(ClosedMotherCasesBreakdown):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'closed_child_cases_breakdown'
    title = 'Closed Child Cases Breakdown'
    total_row_name = "Children cases closed during the time period"

    @property
    def group_by(self):
        return ['reason_for_child_closure']

    @property
    def filters(self):
        filter = super(ClosedMotherCasesBreakdown, self).filters
        filter.append(NOTEQ('reason_for_child_closure', 'empty'))
        return filter

    @property
    def columns(self):
        return [
            DatabaseColumn("Reason for closure", SimpleColumn('reason_for_child_closure')),
            DatabaseColumn("Number", CountUniqueColumn('doc_id'))
        ]

class ImmunizationOverview(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'immunization_overview'
    title = 'Immunization Overview (0 - 2 yrs)'
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Vaccine'), DataTablesColumn('Number'),
                                  DataTablesColumn('Total Eligible'), DataTablesColumn('Percentage'),
                                  DataTablesColumn('Dropout Number'), DataTablesColumn('Dropout Percentage')])

    @property
    def rows(self):
        result = []
        for i in range(0,8):
            dropout = self.data[self.columns[i + 8].slug] - self.data[self.columns[i].slug]
            result.append([{'sort_key': self.columns[i].header, 'html': self.columns[i].header},
                           {'sort_key': self.data[self.columns[i].slug], 'html': self.data[self.columns[i].slug]},
                           {'sort_key': self.data[self.columns[i + 8].slug], 'html': self.data[self.columns[i + 8].slug]},
                           {'sort_key': self.percent_fn(self.data[self.columns[i + 8].slug], self.data[self.columns[i].slug]),
                            'html': self.percent_fn(self.data[self.columns[i + 8].slug], self.data[self.columns[i].slug])},
                           {'sort_key': dropout, 'html': dropout},
                           {'sort_key': self.percent_fn(self.data[self.columns[i + 8].slug], dropout),
                            'html': self.percent_fn(self.data[self.columns[i + 8].slug], dropout)}
            ])
        return result

    @property
    def columns(self):
        return [
            DatabaseColumn("BCG",
                CountUniqueColumn('doc_id', alias="bcg", filters=self.filters + [EQ('bcg', 'yes')])
            ),
            DatabaseColumn("OPV3",
                CountUniqueColumn('doc_id', alias="opv3", filters=self.filters + [EQ('opv0', 'yes')])
            ),
            DatabaseColumn("HEP3",
                CountUniqueColumn('doc_id', alias="hep3", filters=self.filters + [EQ('hepb3', 'yes')])
            ),
            DatabaseColumn("DPT3",
                CountUniqueColumn('doc_id', alias="dpt3", filters=self.filters + [EQ('dpt3', 'yes')])
            ),
            DatabaseColumn("Measles",
                CountUniqueColumn('doc_id', alias="measles", filters=self.filters + [EQ('measles', 'yes')])
            ),
            DatabaseColumn("Fully Immunized in 1st year",
                CountUniqueColumn('doc_id', alias="fully_immunized",
                                  filters=self.filters + [AND([EQ('bcg', 'yes'), EQ('opv0', 'yes'), EQ('hepb0', 'yes'),
                                  EQ('opv1', 'yes'), EQ('hepb1', 'yes'), EQ('dpt1', 'yes'), EQ('opv2', 'yes'), EQ('hepb2', 'yes'),
                                  EQ('dpt2', 'yes'), EQ('opv3', 'yes'), EQ('hepb3', 'yes'), EQ('dpt3', 'yes'), EQ('measles', 'yes')])])
            ),
            DatabaseColumn("DPT-OPT Booster",
                CountUniqueColumn('doc_id', alias="dpt_opv_booster", filters=self.filters + [EQ('dpt_opv_booster', 'yes')])
            ),
            DatabaseColumn("VitA3",
                CountUniqueColumn('doc_id', alias="vita3", filters=self.filters + [EQ('vita3', 'yes')])
            ),
            DatabaseColumn("BCG Total Eligible",
                CountUniqueColumn('doc_id', alias="bcg_eligible"),
            ),
            DatabaseColumn("OPV3 Total Eligible",
                CountUniqueColumn('doc_id', alias="opv3_eligible", filters=self.filters + [LTE('dob', 'days_106')])
            ),
            DatabaseColumn("HEP3 Total Eligible",
                CountUniqueColumn('doc_id', alias="hep3_eligible", filters=self.filters + [LTE('dob', 'days_106')])
            ),
            DatabaseColumn("DPT3 Total Eligible",
                CountUniqueColumn('doc_id', alias="dpt3_eligible", filters=self.filters + [LTE('dob', 'days_106')])
            ),
            DatabaseColumn("Measles Total Eligible",
                CountUniqueColumn('doc_id', alias="measles_eligible", filters=self.filters + [LTE('dob', 'days_273')])
            ),
            DatabaseColumn("Fully Immunized Total Eligible",
                CountUniqueColumn('doc_id', alias="fully_immunized_eligible", filters=self.filters + [LTE('dob', 'days_273')])
            ),
            DatabaseColumn("DPT-OPT Booster Total Eligible",
                CountUniqueColumn('doc_id', alias="dpt_opv_booster_eligible", filters=self.filters + [LTE('dob', 'days_548')])
            ),
            DatabaseColumn("VitA3 Total Eligible",
                CountUniqueColumn('doc_id', alias="vita3_eligible", filters=self.filters + [LTE('dob', 'days_700')])
            )
        ]

class ChildrenDeaths(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'children_deaths'
    title = 'Children Death Details'
    total_row_name = "Total Deaths"
    show_total = True
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def group_by(self):
        return ['type_of_child_death']

    @property
    def rows(self):
        from custom.world_vision import CHILD_DEATH_TYPE
        return self._get_rows(CHILD_DEATH_TYPE, super(ChildrenDeaths, self).rows)

    @property
    def filters(self):
        filter = super(ChildrenDeaths, self).filters
        filter.append(EQ('reason_for_child_closure', 'death'))
        return filter

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Children Death Type'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Reason", SimpleColumn('type_of_child_death')),
            DatabaseColumn("Number", CountUniqueColumn('doc_id'))
        ]

class ChildrenDeathDetails(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'children_death_details'
    title = ''
    show_total = True
    total_row_name = "Total Deaths"
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def group_by(self):
        return ['cause_of_death_child']

    @property
    def rows(self):
        from custom.world_vision import CHILD_CAUSE_OF_DEATH
        return self._get_rows(CHILD_CAUSE_OF_DEATH, super(ChildrenDeathDetails, self).rows)

    @property
    def filters(self):
        filter = super(ChildrenDeathDetails, self).filters
        filter.extend([EQ('reason_for_child_closure', 'death'), NOTEQ('cause_of_death_child', 'empty')])
        return filter

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Cause of death'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Cause of death", SimpleColumn('cause_of_death_child')),
            DatabaseColumn("Number", CountUniqueColumn('doc_id')),
        ]


class MeanColumnWithCasting(BaseColumn):
    aggregate_fn = lambda _, column: func.avg(cast(column, Numeric(7, 5)))


class NutritionMeanMedianBirthWeightDetails(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'children_birth_weights_1'
    title = 'Nutrition Details'

    @property
    def filters(self):
        filters = super(NutritionMeanMedianBirthWeightDetails, self).filters
        filters.append(NOTEQ('weight_birth', 'empty'))
        return filters

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Mean'), DataTablesColumn('Median')])

    @property
    def columns(self):
        return [
            DatabaseColumn("Median Birth Weight",
                MeanColumnWithCasting('weight_birth', alias='mean_birth_weight')
            ),
            DatabaseColumn("Median Birth Weight",
                CustomMedianColumn('weight_birth', alias='median_birth_weight')
            )
        ]

    @property
    def rows(self):
        return [['Birth Weight (kg)',
                 "%.2f" % (self.data['mean_birth_weight']),
                 "%.2f" % (self.data['median_birth_weight'])]
        ]

class NutritionBirthWeightDetails(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'children_birth_details_2'
    title = ''
    show_charts = True
    chart_x_label = ''
    chart_y_label = ''

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Entity'), DataTablesColumn('Number'), DataTablesColumn('Percentage')])

    @property
    def rows(self):
        result = []
        for idx, column in enumerate(self.columns):
            if idx == 0:
                percent = 'n/a'
            else:
                percent = self.percent_fn(self.data['total_birthweight_known'], self.data[column.slug])

            result.append([{'sort_key': column.header, 'html': column.header},
                           {'sort_key': self.data[column.slug], 'html': self.data[column.slug]},
                           {'sort_key': 'percentage', 'html': percent}]
            )
        return result

    @property
    def columns(self):
        columns = [
            DatabaseColumn("Total children with with birthweight known",
                CountUniqueColumn('doc_id',
                    alias="total_birthweight_known",
                    filters=self.filters + [NOTEQ('weight_birth', 'empty')]
                )
            ),
        ]
        columns.extend([
            DatabaseColumn("Birthweight < 2.5 kg",
                CountUniqueColumn('doc_id',
                    alias="total_birthweight_lt_25",
                    filters=self.filters + [AND([LT('weight_birth', 'weight_birth_25'), NOTEQ('weight_birth', 'empty')])]
                )
            ),
            DatabaseColumn("Birthweight >= 2.5 kg",
                CountUniqueColumn('doc_id',
                    alias="total_birthweight_gte_25",
                    filters=self.filters + [AND([GTE('weight_birth', 'weight_birth_25'), NOTEQ('weight_birth', 'empty')])]
                )
            )
        ])
        return columns


class NutritionFeedingDetails(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'children_feeding_details'
    title = ''

    @property
    def headers(self):
        return DataTablesHeader(*[DataTablesColumn('Feeding type'), DataTablesColumn('Number'), DataTablesColumn('Total Eligible'), DataTablesColumn('Percentage')])

    @property
    def rows(self):
        result = []
        for i in range(0,4):
            result.append([{'sort_key': self.columns[2*i].header, 'html': self.columns[2*i].header},
                           {'sort_key': self.data[self.columns[2*i].slug], 'html': self.data[self.columns[2*i].slug]},
                           {'sort_key': self.data[self.columns[2*i+1].slug], 'html': self.data[self.columns[2*i + 1].slug]},
                           {'sort_key': self.percent_fn(self.data[self.columns[2*i + 1].slug], self.data[self.columns[2*i].slug]),
                           'html': self.percent_fn(self.data[self.columns[2*i + 1].slug], self.data[self.columns[2*i].slug])}

            ])
        return result

    @property
    def columns(self):
        return [
            DatabaseColumn("Colostrum feeding",
                CountUniqueColumn('doc_id',
                    alias="colostrum_feeding",
                    filters=self.filters + [EQ('breastfeed_1_hour', 'yes')]
                )
            ),
            DatabaseColumn("Colostrum feeding Total Eligible",
                CountUniqueColumn('doc_id',
                    alias="colostrum_feeding_total_eligible",
                    filters=self.filters + [NOTEQ('breastfeed_1_hour', 'empty')]
                )
            ),

            DatabaseColumn("Exclusive Breastfeeding (EBF)",
                CountUniqueColumn('doc_id',
                    alias="exclusive_breastfeeding",
                    filters=self.filters + [AND([EQ('exclusive_breastfeeding', "yes"), LTE('dob', "days_183")])]
                )
            ),
            DatabaseColumn("Exclusive Breastfeeding (EBF) Total Eligible",
                CountUniqueColumn('doc_id',
                    alias="exclusive_breastfeeding_total_eligible",
                    filters=self.filters + [GTE('dob', 'days_183')]
                )
            ),

            DatabaseColumn("Supplementary feeding",
                CountUniqueColumn('doc_id',
                    alias="supplementary_feeding",
                    filters=self.filters + [AND([EQ('supplementary_feeding_baby', 'yes'), GTE('dob', 'days_182')])]
                )
            ),
            DatabaseColumn("Supplementary feeding Total Eligible",
                CountUniqueColumn('doc_id',
                    alias="supplementary_feeding_total_eligible",
                    filters=self.filters + [GTE('dob', 'days_182')]
                )
            ),

            DatabaseColumn("Complementary feeding",
                CountUniqueColumn('doc_id',
                    alias="complementary_feeding",
                    filters=self.filters + [AND([EQ('comp_breastfeeding', 'yes'), LTE('dob', 'days_183'), GTE('dob', 'days_730')])]
                )
            ),
            DatabaseColumn("Complementary feeding Total Eligible",
                CountUniqueColumn('doc_id',
                    alias="complementary_feeding_total_eligible",
                    filters=self.filters + [AND([LTE('dob', 'days_183'), GTE('dob', 'days_730')])]
                )
            )
        ]


class ChildHealthIndicators(BaseSqlData):
    table_name = "fluff_WorldVisionChildFluff"
    slug = 'Child_health_indicators'
    title = 'Child Health Indicators'

    @property
    def rows(self):
        result = [[{'sort_key': self.columns[0].header, 'html': self.columns[0].header},
                  {'sort_key': self.data[self.columns[0].slug], 'html': self.data[self.columns[0].slug]}],
                  [{'sort_key': self.columns[1].header, 'html': self.columns[1].header},
                  {'sort_key': self.data[self.columns[1].slug], 'html': self.data[self.columns[1].slug]}]]
        for i in range(2,4):
            result.append([{'sort_key': self.columns[i].header, 'html': self.columns[i].header},
                           {'sort_key': self.data[self.columns[i].slug], 'html': self.data[self.columns[i].slug]},
                           {'sort_key': self.percent_fn(self.data[self.columns[1].slug], self.data[self.columns[i].slug]),
                            'html': self.percent_fn(self.data[self.columns[1].slug], self.data[self.columns[i].slug])}])
        return result

    @property
    def columns(self):
        return [
            DatabaseColumn("ARI (Pneumonia) cases",
                CountUniqueColumn('doc_id', alias="ari_cases", filters=self.filters + [EQ('pneumonia_since_last_visit', 'yes')])
            ),
            DatabaseColumn("Diarrhea cases",
                CountUniqueColumn('doc_id', alias="diarrhea_cases", filters=self.filters + [EQ('has_diarrhea_since_last_visit', 'yes')])
            ),
            DatabaseColumn("ORS given during diarrhea",
                CountUniqueColumn('doc_id', alias="ors",
                                  filters=self.filters + [AND([EQ('dairrhea_treated_with_ors', 'yes'), EQ('has_diarrhea_since_last_visit', 'yes')])])
            ),
            DatabaseColumn("Zinc given during diarrhea",
                CountUniqueColumn('doc_id', alias="zinc",
                                  filters=self.filters + [AND([EQ('dairrhea_treated_with_zinc', 'yes'), EQ('has_diarrhea_since_last_visit', 'yes')])])
            )
        ]


class DeliveryPlaceDetailsExtended(DeliveryPlaceDetails):

    @property
    def columns(self):
        columns = super(DeliveryPlaceDetailsExtended, self).columns
        additional_columns = [
            DatabaseColumn("Home deliveries",
                           CountUniqueColumn('doc_id', alias="home_deliveries",
                                             filters=self.filters + [OR([EQ('place_of_birth', 'home'),
                                                                         EQ('place_of_birth', "on_route")])])),
            DatabaseColumn("Other places",
                           CountUniqueColumn('doc_id', alias="other_places",
                                             filters=self.filters + [OR([EQ('place_of_birth', 'empty'),
                                                                         EQ('place_of_birth', "other")])]))
        ]
        columns.extend(additional_columns)
        return columns
