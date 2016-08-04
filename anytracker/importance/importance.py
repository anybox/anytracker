# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class Importance(models.Model):
    """For a task, importance is the added value for the customer,
    For an issue, it is the the impact
    """
    _name = 'anytracker.importance'
    _description = 'Importance of Ticket by method'

    name = fields.Char(
        'Label of the importance',
        required=True,
        size=64,
        translate=True)
    description = fields.Text(
        'Description of the importance',
        translate=True)
    seq = fields.Integer(
        'Importance')
    active = fields.Boolean(
        'Active',
        default=True,
        help='if check, this object is always available')
    method_id = fields.Many2one(
        'anytracker.method',
        'Method',
        required=True,
        ondelete='cascade')
    default = fields.Boolean(
        "Default",
        help="Default importance for new tickets")

    _order = 'method_id, seq'


class Ticket(models.Model):
    _inherit = 'anytracker.ticket'

    @api.depends('importance_id')
    def _get_importance(self):
        for t in self:
            t.importance = t.importance_id.seq if t.importance_id else None

    importance_id = fields.Many2one(
        'anytracker.importance',
        'Importance')
    importance = fields.Integer(
        compute='_get_importance',
        string='Importance',
        type='integer',
        store=True)

    @api.model
    def create(self, values):
        """select the default importance
        """
        METHOD = self.env['anytracker.method']
        IMPORTANCE = self.env['anytracker.importance']
        if not values.get('importance_id'):
            if values.get('parent_id'):
                method = self.browse(values.get('parent_id')).method_id
            else:
                method = METHOD.browse(values['method_id'])
            importances = IMPORTANCE.search([
                ('method_id', '=', method.id),
                ('default', '=', True)])
            if len(importances) > 1:
                raise except_orm(
                    _('Anytracker Configuration Error'),
                    _("Two importances are configured as the default one "
                      "in the '{}' method".format(method.name)))
            if len(importances) == 1:
                values['importance_id'] = importances[0].id
        return super(Ticket, self).create(values)


class Method(models.Model):
    _inherit = 'anytracker.method'

    importance_ids = fields.One2many(
        'anytracker.importance',
        'method_id',
        'Importances',
        help="The importances associated to this method")
