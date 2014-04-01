from anybox.testing.openerp import SharedSetupTransactionCase


class TestExportMindmap(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestExportMindmap, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.notifys = self.registry('anytracker.complexity')
        self.user = self.registry('res.users')
        self.ratings = self.registry('anytracker.rating')
        self.mails = self.registry('mail.mail')
