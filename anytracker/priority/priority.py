# -*- coding: utf-8 -*-

from osv import osv
from osv import fields


class Priority(osv.Model):
    """Priorities represent the timeframe to do tasks.
    It can represent timeboxes, deadlines, milestones
    TODO : define by project, add milestone
    """
    _name = 'anytracker.priority'
    _description = 'Priority of Ticket by method'

    _columns = {
        'name': fields.char('Priority name', required=True, size=64, translate=True),
        'description': fields.text('Priority description', translate=True),
        'seq': fields.integer('Priority', help='a low value is higher priority'),
        'active': fields.boolean('Active', help='if check, this object is always available'),
        'method_id': fields.many2one('anytracker.method', 'Method', required=True),
        #'ticket_id': fields.many2one('anytracker.ticket', 'Project',
        #                             domain="[('parent_id','=',False)]"),
        'deadline': fields.boolean('Force to choose a deadline on the ticket?'),
    }

    _defaults = {
        'active': True,
    }

    _order = 'method_id, seq'


class Ticket(osv.Model):
    _inherit = 'anytracker.ticket'

    def _get_priority(self, cr, uid, ids, fname, args, context=None):
        res = {}
        for ticket in self.browse(cr, uid, ids, context=context):
            res[ticket.id] = ticket.priority_id.seq if ticket.priority_id else 0
        return res

    def onchange_priority(self, cr, uid, ids, prio_id=None, context=None):
        value = {}
        priority_obj = self.pool.get('anytracker.priority')
        priority = priority_obj.read(cr, uid, prio_id, ['deadline'])
        if priority['deadline']:
            return {'value': {'has_deadline': True}}
        return {'value': {'has_deadline': False}}


    _columns = {
        'has_deadline': fields.related('priority_id', 'deadline', type="boolean"),
        'deadline': fields.date('Deadline'),
        'priority_id': fields.many2one('anytracker.priority', 'Priority', required=False),
        'priority': fields.function(
            _get_priority, method=True, string='Priority',
            type='integer', store=True),
    }
