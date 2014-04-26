# -*- coding: utf-8 -*-
from anybox.testing.openerp import SharedSetupTransactionCase
from openerp import modules
from openerp.osv import osv
import base64
import unittest
from datetime import date


def get_mindmap_binary():
    fp = open(modules.get_module_resource('anytracker', 'mindmap/tests/mock_mindmap.mm'), 'rb')
    return base64.b64encode(fp.read())


class TestImportExportMindmap(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = ('ticket_toexport.xml',)

    @classmethod
    def initTestData(cls):
        super(TestImportExportMindmap, cls).initTestData()
        cls.tickets = cls.registry('anytracker.ticket')
        cls.notifys = cls.registry('anytracker.complexity')
        cls.user = cls.registry('res.users')
        cls.ratings = cls.registry('anytracker.rating')
        cls.mails = cls.registry('mail.mail')
        cls.wiz_import = cls.registry('import.mindmap.wizard')
        cls.wiz_export = cls.registry('export.mindmap.wizard')
        cls.green = cls.ref('anytracker.complexity_implementation_green')
        cls.red = cls.ref('anytracker.complexity_implementation_red')
        cls.orange = cls.ref('anytracker.complexity_implementation_orange')
        cls.maintenance = cls.ref('anytracker.method_maintenance')
        cls.main_ticket = cls.ref('anytracker.anytracker_ticket-droit_dacces_application_mlf')

    def create_wizard_import(self, **kw):
        values = dict(ticket_id=False, import_method='insert',
                      mindmap_content=get_mindmap_binary(), green_complexity=self.green,
                      orange_complexity=self.orange, red_complexity=self.red,
                      method_id=self.maintenance)
        if kw:
            values.update(kw)
        return self.wiz_import.create(self.cr, self.uid, values)

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

    def test_wizard_import_mindmap(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_import()
        self.wiz_import.execute_import(cr, uid, wiz_id)

    def test_import_mindmap(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_import()
        self.wiz_import.execute_import(cr, uid, wiz_id)
        ticket_id = self.tickets.search(
            cr, uid, [('name', '=', u"Droit d'accés application mlf"), ('parent_id', '=', False)])[0]
        ticket_ids = self.tickets.search(cr, uid, [('parent_id', 'child_of', ticket_id)])
        self.assertEqual(len(ticket_ids), 6)

    def test_bug_with_update_import_method_and_no_ticket_id(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.create_wizard_import(import_method='update')
        try:
            self.wiz_import.execute_import(cr, uid, wiz_id)
            self.fail()
        except osv.except_osv:
            return
        self.fail()
