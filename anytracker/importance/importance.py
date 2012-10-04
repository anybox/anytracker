# -*- coding: utf-8 -*-

from osv import osv
from osv import fields


class TicketImportance(osv.Model):
    _name = 'anytracker.importance'
    _description = 'Importance of Ticket by methode'

    _columns = {
        'name': fields.char('Label of the importance', required=True, size=64),
        'seq': fields.integer('Importance'),
        'active': fields.boolean('Active', help='if check, this object is always available'),
        'method_id': fields.many2one('anytracker.method', 'Method', required=True),
    }

    _defaults = {
        'active': lambda *a: True,
    }

    _order = 'method_id,seq'

class Ticket(osv.Model):
    _inherit = 'anytracker.ticket'

    def _get_importance_seq(self, cr, uid, ids, fname, args, context=None):
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            res[ticket.id] = ticket.importance_id.seq if ticket.importance_id else 0
        return res

    _columns = {
        'importance_id': fields.many2one('anytracker.importance', 'Importance', required=True),
        'seq': fields.function(_get_importance_seq,
                            method=True,
                            string='Importance (Number)',
                            type='integer',
                            store=True),
    }

    _order = 'method_id,seq'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
