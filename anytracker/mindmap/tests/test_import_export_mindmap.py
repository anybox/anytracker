# -*- coding: utf-8 -*-
import base64

from anybox.testing.openerp import SharedSetupTransactionCase
from odoo import modules
from odoo.exceptions import except_orm


def get_mindmap_binary():
    with open(modules.get_module_resource(
              'anytracker', 'mindmap/tests/mock_mindmap.mm'), 'rb') as fp:
        return base64.b64encode(fp.read())


class TestImportExportMindmap(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = ('ticket_toexport.xml',)

    @classmethod
    def initTestData(cls):
        super(TestImportExportMindmap, cls).initTestData()
        cls.TICKET = cls.env['anytracker.ticket']
        cls.WIZIMP = cls.env['import.mindmap.wizard']
        cls.WIZEXP = cls.env['export.mindmap.wizard']
        cls.green = cls.env.ref('anytracker.complexity_implementation_green')
        cls.red = cls.env.ref('anytracker.complexity_implementation_red')
        cls.orange = cls.env.ref('anytracker.complexity_implementation_orange')
        cls.maintenance = cls.env.ref('anytracker.method_maintenance')
        cls.main_ticket = cls.env.ref(
            'anytracker.anytracker_ticket-droit_dacces_application_mlf')

    def create_wizard_import(self, **kw):
        values = {
            'ticket_id': False,
            'import_method': 'insert',
            'mindmap_content': get_mindmap_binary(),
            'green_complexity': self.green.id,
            'orange_complexity': self.orange.id,
            'red_complexity': self.red.id,
            'method_id': self.maintenance.id}
        values.update(kw)
        return self.WIZIMP.create(values)

    def create_wizard_export(self, **kw):
        values = {
            'ticket_id': self.main_ticket.id,
            'mindmap_file': 'mock.mm',
            'green_complexity': self.green.id,
            'orange_complexity': self.orange.id,
            'red_complexity': self.red.id}
        values.update(kw)
        return self.WIZEXP.create(values)

    def test_wizard_export_mindmap(self):
        self.create_wizard_export().execute_export()

    def test_wizard_import_mindmap(self):
        #self.create_wizard_import().execute_import()
        self.create_wizard_import()

    def test_import_mindmap(self):
        #self.create_wizard_import().execute_import()
        self.create_wizard_import()
        ticket = self.TICKET.search([
            ('name', '=', u"Droit d'accés application mlf (test)"),
            ('parent_id', '=', False)])[0]
        tickets = self.TICKET.search([('parent_id', 'child_of', ticket.id)])
        self.assertEqual(len(tickets), 6)

    def test_bug_with_update_import_method_and_no_ticket_id(self):
        try:
            #self.create_wizard_import(import_method='update').execute_import()
            self.create_wizard_import(import_method='update')
            self.fail()
        except except_orm:
            return
        self.fail()
