# -*- coding: utf-8 -*-
from odoo import models, fields


class serve_mindmap_wizard(models.TransientModel):

    _name = 'serve.mindmap.wizard'
    _description = 'Serve mindmap generated file'

    mindmap_binary = fields.Binary("File to download")
    mindmap_filename = fields.Char("Filename", size=64)

    def execute_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
