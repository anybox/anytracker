# -*- coding: utf-8 -*-
from openerp.osv import osv, fields


class serve_mindmap_wizard(osv.TransientModel):
    _name = 'serve.mindmap.wizard'
    _description = 'Serve mindmap generated file'
    _columns = {
        'mindmap_binary': fields.binary("File to download"),
        'mindmap_filename': fields.char("Filename", size=64),
    }

    def execute_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
