from anybox.testing.openerp import SharedSetupTransactionCase
from openerp import netsvc


class ReportTestCase(SharedSetupTransactionCase):

    _report_name = ''
    _report_base_model = ''

    @classmethod
    def initTestData(self):
        super(ReportTestCase, self).initTestData()
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
