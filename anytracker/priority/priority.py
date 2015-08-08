# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class Priority(models.Model):
    """Priorities represent the timeframe to do tasks.
    It can represent timeboxes, deadlines, milestones
    TODO : add milestone
    """
    _name = 'anytracker.priority'
    _description = 'Priority of Ticket by method'

    name = fields.Char('Priority name', required=True, size=64, translate=True)
    description = fields.Text('Priority description', translate=True)
    seq = fields.Integer('Priority', help='a low value is higher priority')
    active = fields.Boolean('Active', help='if check, this object is always available')
    method_id = fields.Many2one('anytracker.method', string='Method',
                                required=True, ondelete='cascade')
    deadline = fields.Boolean('Force to choose a deadline on the ticket?')
    date = fields.Date('Milestone')

    _defaults = {
        'active': True,
    }

    _order = 'method_id, seq'


class Ticket(models.Model):
    _inherit = 'anytracker.ticket'

    def _get_priority(self, cr, uid, ids, fname, args, context=None):
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            res[ticket.id] = ticket.priority_id.seq if ticket.priority_id else 0
        return res

    def onchange_priority(self, cr, uid, ids, prio_id=None, context=None):
        if not prio_id:
            return {}
        priority_obj = self.pool.get('anytracker.priority')
        priority = priority_obj.read(cr, uid, prio_id, ['deadline'])
        if priority['deadline']:
            return {'value': {'has_deadline': True}}
        return {'value': {'has_deadline': False}}

    has_deadline = fields.Boolean('priority_id.deadline', type="boolean")
    deadline = fields.Date('Deadline')
    priority_id = fields.Many2one('anytracker.priority', 'Priority', required=False)
    priority = fields.Integer(
        compute='_get_priority', method=True, string='Priority', store=True)


class Method(models.Model):
    _inherit = 'anytracker.method'

    priority_ids = fields.One2many(
        'anytracker.priority',
        'method_id',
        string='Priorities',
        help="The priorities associated to this method")
