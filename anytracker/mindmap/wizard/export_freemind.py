from osv import osv, fields
from .freemind_parse import FreemindWriterHandler
from .freemind_parse import FreemindParser
import StringIO


# TODO complexity icon, mindmapfile to binary?, richtext content generation
class export_freemind_wizard(osv.TransientModel):
    _name = 'export.freemind.wizard'
    _description = 'export freemind .mm file for generate by anytracker tree'
    _columns = {
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket'),
        'mindmap_file': fields.char('Path of file to write', 256),
        'green_complexity': fields.many2one('anytracker.complexity', 'green complexity'),
        'orange_complexity': fields.many2one('anytracker.complexity', 'orange complexity'),
        'red_complexity': fields.many2one('anytracker.complexity', 'red complexity'),
    }

    def execute_export(self, cr, uid, ids, context=None):
        '''Launch export of nn file to freemind'''
        any_tick_complexity_pool = self.pool.get('anytracker.complexity')
        serv_freemind_wizard = self.pool.get('serve.freemind.wizard')
        ir_action = self.pool.get('ir.actions.act_window')
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
                raise osv.except_osv('Error', 'Please select a ticket to export')

            fp = StringIO.StringIO()

            writer_handler = FreemindWriterHandler(cr, uid, self.pool, fp)
            writer_parser = FreemindParser(cr, uid, self.pool, writer_handler,
                                           ticket_id, complexity_dict)
            writer_parser.parse(cr, uid)

            record_id = serv_freemind_wizard.create(
                cr, uid, dict(mindmap_binary_file=fp.getvalues()))

            fp.close()
            res_id = mod_obj.get_object_reference(cr, uid, 'anytracker', 'action_serve_freemind_file')
            res_r = ir_action.read(cr, uid, res_id, [], context=context)
            import pdb
            pdb.set_trace()
            return {
                'name': 'Provide your popup window name',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [res and res[1] or False],
                'res_model': 'your.popup.model.name',
                'context': "{}",
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'res_id': record_id  or False,
            }


