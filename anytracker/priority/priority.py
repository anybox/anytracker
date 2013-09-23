# -*- coding: utf-8 -*-

from osv import osv
from osv import fields


class Priority(osv.Model):
    """Priority to perform tasks/projects/issues,
    priorities are set by methods.
    """
    _name = 'anytracker.priority'
    _description = 'Priority of Ticket by method'

    _columns = {
        'name': fields.char('Priority name', required=True, size=64, translate=True),
        'description': fields.text('Priority description', translate=True),
        'seq': fields.integer('Priority'),
        'active': fields.boolean('Active', help='if check, this object is always available'),
        'method_id': fields.many2one('anytracker.method', 'Method', required=True),
    }

    _defaults = {
        'active': True,
    }

    _order = 'method_id,seq'


class Ticket(osv.Model):
    _inherit = 'anytracker.ticket'

    def _get_priority_seq(self, cr, uid, ids, fname, args, context=None):
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            res[ticket.id] = ticket.priority_id.seq if ticket.priority_id else 0
        return res

    _columns = {
        'priority_id': fields.many2one('anytracker.priority', 'Priority', required=False, translate=True),
        'seq': fields.function(
            _get_priority_seq, method=True, string='Priority (Number)',
            type='integer', store=True),
    }

    _order = 'seq, create_date desc'
