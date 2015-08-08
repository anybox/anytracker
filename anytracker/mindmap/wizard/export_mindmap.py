from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from .mindmap_parse import FreemindWriterHandler
from .mindmap_parse import FreemindParser
import StringIO
from base64 import b64encode


# TODO complexity icon, mindmapfile to binary?, richtext content generation
class export_mindmap_wizard(models.TransientModel):
    _name = 'export.mindmap.wizard'
    _description = 'export mindmap .mm file for generate by anytracker tree'

    ticket_id = fields.Many2one('anytracker.ticket', 'Ticket', required=True)
    mindmap_file = fields.Char('filename to download', siez=256, required=True)
    green_complexity = fields.Many2one('anytracker.complexity', 'green complexity',
                                       required=True)
    orange_complexity = fields.Many2one('anytracker.complexity', 'orange complexity',
                                        required=True)
    red_complexity = fields.Many2one('anytracker.complexity', 'red complexity', required=True)

    _defaults = dict(mindmap_file='mindmap.mm')

    def execute_export(self, cr, uid, ids, context=None):
        '''Launch export of nn file to mindmap'''
        if isinstance(ids, (int, long)):
            ids = [ids]
        any_tick_complexity_pool = self.pool.get('anytracker.complexity')
        serv_mindmap_wizard = self.pool.get('serve.mindmap.wizard')
        mod_obj = self.pool.get('ir.model.data')
        for wizard in self.browse(cr, uid, ids, context=context):
            complexity_dict = {
                'green_complexity_id':
                    wizard.green_complexity.id
                    or any_tick_complexity_pool.search(cr, uid, [('value', '=', 3)])[0],
                'orange_complexity_id': wizard.orange_complexity.id
                                        or any_tick_complexity_pool.search(cr, uid, [('value', '=', 21)])[0],
                'red_complexity_id': wizard.red_complexity.id
                                     or any_tick_complexity_pool.search(cr, uid, [('value', '=', 3)])[0],
            }
            ticket_id = wizard.ticket_id and wizard.ticket_id.id or False
            if not ticket_id:
                raise orm.except_orm('Error', 'Please select a ticket to export')

            fp = StringIO.StringIO()

            writer_handler = FreemindWriterHandler(cr, uid, self.pool, fp)
            writer_parser = FreemindParser(cr, uid, self.pool, writer_handler,
                                           ticket_id, complexity_dict)
            writer_parser.parse(cr, uid)

            record_id = serv_mindmap_wizard.create(
                cr, uid, dict(mindmap_binary=b64encode(fp.getvalue()),
                              mindmap_filename=wizard.mindmap_file))

            fp.close()
            _, res = mod_obj.get_object_reference(cr, uid, 'anytracker', 'view_serve_mindmap_form')
            return {
                'name': 'Download mindmap wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': res,
                'res_model': 'serve.mindmap.wizard',
                'context': "{}",
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': record_id or False,
            }
