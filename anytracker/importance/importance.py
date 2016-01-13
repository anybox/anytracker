# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class Importance(models.Model):
    """For a task, importance is the added value for the customer,
    For an issue, it is the the impact
    """
    _name = 'anytracker.importance'
    _description = 'Importance of Ticket by method'

    name = fields.Char('Label of the importance', required=True, size=64, translate=True)
    description = fields.Text('Description of the importance', translate=True)
    seq = fields.Integer('Importance')
    active = fields.Boolean('Active', help='if check, this object is always available')
    method_id = fields.Many2one('anytracker.method', 'Method',
                                required=True, ondelete='cascade')

    _defaults = {
        'active': True,
    }

    _order = 'method_id, seq'


class Ticket(models.Model):
    _inherit = 'anytracker.ticket'

    def _get_importance(self, cr, uid, ids, fname, args, context=None):
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            res[ticket.id] = ticket.importance_id.seq if ticket.importance_id else 0
        return res

    importance_id = fields.Many2one('anytracker.importance', 'Importance')
    importance = fields.Integer(
        compute='_get_importance', method=True, string='Importance',
        type='integer', store=True)


class Method(models.Model):
    _inherit = 'anytracker.method'

    importance_ids = fields.One2many(
        'anytracker.importance',
        'method_id',
        'Importances',
        help="The importances associated to this method")
