from anybox.testing.openerp import SharedSetupTransactionCase
from openerp import modules
import base64
import unittest
from datetime import date


def get_mindmap_binary():
    fp = open(modules.get_module_resource('anytracker', 'mindmap/tests/mock_mindmap.mm'), 'rb')
    return base64.b64encode(fp.read())


class TestImportMindmap(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(cls):
        super(TestImportMindmap, cls).initTestData()
        cls.tickets = cls.registry('anytracker.ticket')
        cls.notifys = cls.registry('anytracker.complexity')
        cls.user = cls.registry('res.users')
        cls.ratings = cls.registry('anytracker.rating')
        cls.mails = cls.registry('mail.mail')
        cls.wiz_import = cls.registry('import.mindmap.wizard')
        cls.green = cls.ref('anytracker.complexity_implementation_green')
        cls.red = cls.ref('anytracker.complexity_implementation_red')
        cls.orange = cls.ref('anytracker.complexity_implementation_orange')
        cls.maintenance = cls.ref('anytracker.method_maintenance')

    def create_wizard_import(self, **kw):
        values = dict(ticket_id=False, import_method='insert',
                      mindmap_content=get_mindmap_binary(), green_complexity=self.green,
                      orange_complexity=self.orange, red_complexity=self.red,
                      method_id=self.maintenance)
        if kw:
            values.update(kw)
        return self.wiz_import.create(self.cr, self.uid, values)

    def test_wizard_import_mindmap(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_import()
        self.wiz_import.execute_import(cr, uid, wiz_id)

    def test_import_mindmap(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_import()
        self.wiz_import.execute_import(cr, uid, wiz_id)
        ticket_ids = self.tickets.search(cr, uid, [])
        self.assertEqual(len(ticket_ids), 6)

    @unittest.skipIf(date.today() < date(2014, 5, 5), "Must be fix")
    def test_bug_with_update_import_method_and_no_ticket_id(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_import(import_method='update')
        self.wiz_import.execute_import(cr, uid, wiz_id)
