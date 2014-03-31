# -*- coding: utf-8 -*-
from osv import osv, fields


class serve_freemind_wizard(osv.TransientModel):
    _name = 'serve.freemind.wizard'
    _description = 'Serve freemind generated file'
    _columns = {
        'mindmap_binary_file': fields.binary("File to download"),
    }

    def execute_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
