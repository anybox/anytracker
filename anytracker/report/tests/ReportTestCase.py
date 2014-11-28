from anybox.testing.openerp import SharedSetupTransactionCase
from openerp import netsvc
from datetime import datetime
from osv import osv


class ReportTestCase(SharedSetupTransactionCase):

    _report_name = ''
    _report_base_model = ''

    @classmethod
    def initTestData(self):
        super(ReportTestCase, self).initTestData()
        # need to test _report_name, if it's not define, nose is currently running ReportTestCase
        # not inherits classes
        if self._report_name:
            self.reportService = netsvc.LocalService('report.' + self._report_name)
            self.parser = self.reportService.parser(self.cr, self.uid, self.reportService.name,
                                                    context=None)

    def generateReport(self, ids, data={}, context=None):
        """Generate the report and return it as a tuple (result, format)
            where `result` is the report document and `format` is generaly the file extension.
        """
        if not isinstance(data, dict):
            data = dict()
        data.update({'model': self. _report_base_model})
        return self.reportService.create(self.cr, self.uid, ids, data, context=context)

    def getParser(self):
        return self.parser

    def test_displayLocaleDateTime(self):
        """All reports that use ir_header_webkit_base_anytracker should test displayLocaleDateTime
        """
        # need to test _report_name, if it's not define, nose is currently running ReportTestCase
        # not inherits classes
        if self._report_name:
            self.assertEqual(self.getParser()._displayLocaleDateTime('UTC'),
                             datetime.now().strftime('%d/%m/%Y %H:%M'))
            self.assertEqual(self.getParser()._displayLocaleDateTime('UTC', '%Y --- %M'),
                             datetime.now().strftime('%Y --- %M'))
            self.assertRaises(
                osv.except_osv,
                self.getParser()._displayLocaleDateTime,
                'unvalid value test')
