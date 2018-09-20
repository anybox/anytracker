from io import StringIO
from base64 import b64encode

from odoo import models, fields
from odoo.exceptions import except_orm
from .mindmap_parse import FreemindWriterHandler
from .mindmap_parse import FreemindParser


# TODO complexity icon, mindmapfile to binary?, richtext content generation
class export_mindmap_wizard(models.TransientModel):
    _name = 'export.mindmap.wizard'
    _description = 'export mindmap .mm file for generate by anytracker tree'

    ticket_id = fields.Many2one(
        'anytracker.ticket',
        'Ticket',
        required=True)
    mindmap_file = fields.Char(
        'filename to download',
        size=256,
        default='mindmap.mm',
        required=True)
    green_complexity = fields.Many2one(
        'anytracker.complexity',
        'green complexity',
        required=True)
    orange_complexity = fields.Many2one(
        'anytracker.complexity',
        'orange complexity',
        required=True)
    red_complexity = fields.Many2one(
        'anytracker.complexity',
        'red complexity',
        required=True)

    def execute_export(self):
        '''Launch export of nn file to mindmap'''
        COMPLEXITY = self.env['anytracker.complexity']
        DOWNLOADWIZ = self.env['serve.mindmap.wizard']
        for wizard in self:
            wizard.complexity_dict = {
                'green_complexity_id':
                    wizard.green_complexity.id
                    or COMPLEXITY.search([('value', '=', 3)])[0].id,
                'orange_complexity_id':
                    wizard.orange_complexity.id
                    or COMPLEXITY.search([('value', '=', 21)])[0].id,
                'red_complexity_id':
                    wizard.red_complexity.id
                    or COMPLEXITY.search([('value', '=', 3)])[0].id,
            }
            if not wizard.ticket_id:
                raise except_orm('Error', 'Please select a ticket to export')

            fp = StringIO()
            FreemindParser(FreemindWriterHandler(fp), wizard).parse()
            download_wiz = DOWNLOADWIZ.create({
                'mindmap_binary': b64encode(fp.getvalue()),
                'mindmap_filename': wizard.mindmap_file})
            fp.close()

            view_id = self.env.ref('anytracker.view_serve_mindmap_form').id
            return {
                'name': 'Download mindmap wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'res_model': 'serve.mindmap.wizard',
                'context': "{}",
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': download_wiz or False,
            }
