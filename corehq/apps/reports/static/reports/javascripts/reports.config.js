var HQReport = function (options) {
    'use strict';
    var self = this;
    self.domain = options.domain;
    self.datespan = options.datespan;
    self.filterSet = options.filterSet || false;
    self.needsFilters = options.needsFilters || false;
    self.filterAccordion = options.filterAccordion || "#reportFilters";
    self.filterSubmitButton = options.filterSubmitButton || $('#paramSelectorForm button[type="submit"]');
    self.toggleFiltersButton = options.toggleFiltersButton || "#toggle-report-filters";
    self.exportReportButton = options.exportReportButton || "#export-report-excel";
    self.emailReportButton = options.emailReportButton || "#email-report";
    self.emailReportModal = options.emailReportModal || "#email-report-modal";
    self.urlRoot = options.urlRoot;
    self.slug = options.slug;
    self.subReportSlug = options.subReportSlug;
    self.type = options.type;

    self.toggleFiltersCookie = self.domain+'.hqreport.toggleFilterState';
    self.datespanCookie = self.domain+".hqreport.filterSetting.test.datespan";

    self.initialLoad = true;

    self.emailReportViewModel = new EmailReportViewModel();

    self.init = function () {
        $(function () {
            checkFilterAccordionToggleState();

            $(self.exportReportButton).click(function (e) {
                e.preventDefault();
                window.location.href = get_report_render_url("export");
            });

            $(self.emailReportButton).click(function (e) {
                self.emailReportViewModel.setConfigBeingEmailed();
            });

            self.resetFilterState();
            if (self.needsFilters) {
                self.filterSubmitButton.button('reset').addClass('btn-primary');
            }

            ko.applyBindings(self.emailReportViewModel, $(self.emailReportModal).get(0));
        });
    };

    self.handleTabularReportCookies = function (reportDatatable) {
        var defaultRowsCookieName = self.domain+'.hqreport.tabularSetting.defaultRows',
            savedPath = window.location.pathname;
        var defaultRowsCookie = ''+$.cookie(defaultRowsCookieName);
        reportDatatable.defaultRows = parseInt(defaultRowsCookie) || reportDatatable.defaultRows;

        $(reportDatatable.dataTableElem).on('hqreport.tabular.lengthChange', function (event, value) {
            $.cookie(defaultRowsCookieName, value,
                {path: savedPath, expires: 2});
        });
    };

    self.saveDatespanToCookie = function () {
        if (self.datespan) {
            $.cookie(self.datespanCookie+'.startdate', self.datespan.startdate,
                {path: self.urlRoot, expires: 1});
            $.cookie(self.datespanCookie+'.enddate', self.datespan.enddate,
                {path: self.urlRoot, expires: 1});
        }
    };

    self.loadDatespanFromCookie = function () {
        if (self.datespan) {
            var cookie_startdate = $.cookie(self.datespanCookie+'.startdate'),
                cookie_enddate = $.cookie(self.datespanCookie+'.enddate'),
                load_success = false;

            if (cookie_enddate && cookie_startdate) {
                load_success = true;
                self.datespan.startdate = cookie_startdate;
                self.datespan.enddate = cookie_enddate;
            }
        }
        return load_success;
    };

    var checkFilterAccordionToggleState = function () {
        var _setShowFilterCookie = function (show) {
            var showStr = show ? 'in' : '';
            $.cookie(self.toggleFiltersCookie, showStr, {path: self.urlRoot, expires: 1});
        };
        
        if ($.cookie(self.toggleFiltersCookie) === null) {
            // default to showing filters
            _setShowFilterCookie(true);
        }
        $(self.filterAccordion).addClass($.cookie(self.toggleFiltersCookie));
        
        if ($.cookie(self.toggleFiltersCookie) == 'in') {
            $(self.toggleFiltersButton).button('close');
        } else {
            $(self.toggleFiltersButton).button('open');
        }

        $(self.filterAccordion).on('hidden', function (data) {
            if (!(data.target && $(data.target).hasClass('modal'))) {
                _setShowFilterCookie(true);
                $(self.toggleFiltersButton).button('open');
            }
        });

        $(self.filterAccordion).on('show', function () {
            _setShowFilterCookie(true);
            $(self.toggleFiltersButton).button('close');
        });

    };

    $(self.filterAccordion).on('hqreport.filter.datespan.startdate', function(event, value) {
        self.datespan.startdate = value;
    });

    $(self.filterAccordion).on('hqreport.filter.datespan.enddate', function(event, value) {
        self.datespan.enddate = value;
    });

    self.resetFilterState = function () {
        $('#paramSelectorForm fieldset button, #paramSelectorForm fieldset span[data-dropdown="dropdown"]').click(function() {
            $('#paramSelectorForm button[type="submit"]').button('reset').addClass('btn-primary');
        });
        $('#paramSelectorForm fieldset').change(function () {
            $('#paramSelectorForm button[type="submit"]').button('reset').addClass('btn-primary');
        });
    };

    function get_report_render_url(render_type, additionalParams) {
        var params = window.location.search.substr(1);
        if (params.length <= 1) {
            if (self.loadDatespanFromCookie()) {
                params = "startdate="+self.datespan.startdate+
                    "&enddate="+self.datespan.enddate;
            }
        }
        return window.location.pathname.replace(self.urlRoot,
            self.urlRoot+render_type+"/")+"?"+params + (additionalParams == undefined ? "" : "&" + additionalParams);
    };

    function EmailReportViewModel() {
        var self = this;

        self.modalTitle = "Email report";
        self.configBeingEmailed = ko.observable();

        self.send_to_owner = ko.observable(true);
        self.subject = ko.observable("Once of Report");
        self.recipient_emails = ko.observable();
        self.notes = ko.observable();

        self.setConfigBeingEmailed = function () {
            self.configBeingEmailed({});
        }

        self.unsetConfigBeingEmailed = function() {
            self.configBeingEmailed(undefined);
        }

        self.unwrap = function () {
            var data = ko.mapping.toJS(self, {
                ignore: ['modalTitle', 'configBeingEmailed', 'setConfigBeingEmailed',
                'unsetConfigBeingEmailed', 'sendEmail', 'unwrap']
            });

            for (var i in data) {
                if (data[i] === null || data[i] === undefined) delete data[i];
            }
            return data;
        }

        self.sendEmail = function(data, event) {
            $.get(get_report_render_url("email_onceoff", $.param(self.unwrap())))
                .done(function() {
                    alert("Report successfully emailed.");
                    self.unsetConfigBeingEmailed();
                })
                .fail(function() { alert("An error occurred, please try again."); });
        }
    };
};