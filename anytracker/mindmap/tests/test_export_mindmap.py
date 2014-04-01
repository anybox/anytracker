from anybox.testing.openerp import SharedSetupTransactionCase


class TestExportMindmap(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = ('ticket_toexport.xml',)

    @classmethod
    def initTestData(cls):
        super(TestExportMindmap, cls).initTestData()
        cls.tickets = cls.registry('anytracker.ticket')
        cls.notifys = cls.registry('anytracker.complexity')
        cls.user = cls.registry('res.users')
        cls.ratings = cls.registry('anytracker.rating')
        cls.mails = cls.registry('mail.mail')
        cls.wiz_export = cls.registry('export.mindmap.wizard')
        cls.green = cls.ref('anytracker.complexity_implementation_green')
        cls.red = cls.ref('anytracker.complexity_implementation_red')
        cls.orange = cls.ref('anytracker.complexity_implementation_orange')
        cls.maintenance = cls.ref('anytracker.method_maintenance')
        cls.main_ticket = cls.ref('anytracker.anytracker_ticket-droit_dacces_application_mlf')

    def create_wizard_export(self, **kw):
        values = dict(ticket_id=self.main_ticket, mindmap_file='mock.mm',
                      green_complexity=self.green, orange_complexity=self.orange,
                      red_complexity=self.red)
        if kw:
            values.update(kw)
        return self.wiz_export.create(self.cr, self.uid, values)

    def test_export_mindmap(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_export()
        self.wiz_export.execute_export(cr, uid, wiz_id)

    def test_wizard_export_mindmap(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_export()
        self.wiz_export.execute_export(cr, uid, wiz_id)
