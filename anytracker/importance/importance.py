# -*- coding: utf-8 -*-

from osv import osv
from osv import fields


class Importance(osv.Model):
    """For a task, importance is the added value for the customer,
    For an issue, it is the the impact
    """
    _name = 'anytracker.importance'
    _description = 'Importance of Ticket by method'

    _columns = {
        'name': fields.char('Label of the importance', required=True, size=64, translate=True),
        'description': fields.text('Description of the importance', translate=True),
        'seq': fields.integer('Importance'),
        'active': fields.boolean('Active', help='if check, this object is always available'),
        'method_id': fields.many2one('anytracker.method', 'Method', required=True),
    }

    _defaults = {
        'active': True,
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
        'importance_id': fields.many2one('anytracker.importance', 'Importance', required=False),
        'seq': fields.function(
            _get_importance_seq, method=True, string='Importance (Number)',
            type='integer', store=True),
    }

    _order = 'seq desc,create_date desc'
