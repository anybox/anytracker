# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class Importance(models.Model):
    """For a task, importance is the added value for the customer,
    For an issue, it is the the impact
    """
    _name = 'anytracker.importance'
    _description = 'Importance of Ticket by method'
    _order = 'method_id, seq DESC'

    name = fields.Char(
        'Label of the importance',
        required=True,
        size=64,
        translate=True)
    description = fields.Text(
        'Description of the importance',
        translate=True)
    seq = fields.Integer(
        'Importance',
        help="A higher value is higher importance")
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
    color = fields.Char(
        "Color",
        help="Color (in any CSS format) used to represent this importance")

    _order = 'method_id, seq DESC'

    @api.multi
    def write(self, vals):
        """ in case the sequence is changed,
        we must change all the stored importances on tickets
        """
        seq = vals.get('seq')
        if seq:
            self.env['anytracker.ticket'].search(
                [('importance_id', '=', self.id)]).write(
                    {'importance': seq})
        return super(Importance, self).write(vals)


class Ticket(models.Model):
    _inherit = 'anytracker.ticket'

    importance_id = fields.Many2one(
        'anytracker.importance',
        'Importance')
    importance = fields.Integer(
        compute='_get_importance',
        string='Importance',
        type='integer',
        store=True)
    importance_color = fields.Char(
        string='Importance color',
        compute='_importance_color')

    @api.depends('importance_id')
    def _get_importance(self):
        for t in self:
            t.importance = t.importance_id.seq if t.importance_id else None

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

    @api.depends('importance_id')
    def _importance_color(self):
        for t in self:
            if t.importance_id:
                t.importance_color = t.importance_id.color


class Method(models.Model):
    _inherit = 'anytracker.method'

    importance_ids = fields.One2many(
        'anytracker.importance',
        'method_id',
        'Importances',
        help="The importances associated to this method")
