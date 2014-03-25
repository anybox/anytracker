# -*- coding: utf-8 -*-

from openerp.osv import osv, fields


class WebLiveConfig(osv.TransientModel):
    _inherit = 'web.live.config'

    _columns = {
        'module_live_anytracker': fields.boolean('CRM'),
        'live_anytracker_ticket_kanban': fields.boolean(
            'Anytracker ticket / Kanban', required=True, module='live_anytracker',
            view_type='kanban'),
    }
