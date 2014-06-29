# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields


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
        'method_id': fields.many2one('anytracker.method', 'Method',
                                     required=True, ondelete='cascade'),
    }

    _defaults = {
        'active': True,
    }

    _order = 'method_id, seq'

    _sql_constraint = [
        ('seq_uniq', 'unique(method_id, seq)', 'Importance (seq) must be different from others')]


class Ticket(osv.Model):
    _inherit = 'anytracker.ticket'

    def _get_importance(self, cr, uid, ids, fname, args, context=None):
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            res[ticket.id] = ticket.importance_id.seq if ticket.importance_id else 0
        return res

    _columns = {
        'importance_id': fields.many2one('anytracker.importance', 'Importance', required=False),
        'importance': fields.function(
            _get_importance, method=True, string='Importance',
            type='integer', store=True),
    }


class Method(osv.Model):
    _inherit = 'anytracker.method'
    _columns = {
        'importance_ids': fields.one2many(
            'anytracker.importance',
            'method_id',
            'Importances',
            help="The importances associated to this method"),
    }
