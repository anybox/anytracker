# -*- coding: utf-8 -*-

from osv import osv
from osv import fields
import time


class Assignment(osv.Model):
    """ Several users can be assigned to a ticket at different stages
    So we have a separated object for assignment
    """
    _name = 'anytracker.assignment'
    _description = 'Assignments'
    _rec_name = 'user_id'
    _order = 'date DESC'

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=True),
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket', required=True),
        'stage_id': fields.many2one('anytracker.stage', 'Stage', required=True),
        'date': fields.datetime('Date', help='Assignment date', required=True),
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }


class Ticket(osv.Model):
    """ Add assignment to tickets
    """
    _inherit = 'anytracker.ticket'

    def _get_assignment(self, cr, uid, ids, field_name, args, context=None):
        """ Return the last assignment of the ticket for the current stage
        """
        if not context: context = {}
        as_pool = self.pool.get('anytracker.assignment')
        assignments = {}
        for ticket in self.read(cr, uid, ids, ['stage_id'], context):
            assignments[ticket['id']] = False
            assignment_ids = as_pool.search(cr, uid,
                            [('stage_id', '=', ticket['stage_id'][0]),
                             ('ticket_id', '=', ticket['id'])],
                            context=context)
            if not assignment_ids:
                continue
            # assignments are ordered by 'date DESC' so we take the last
            assignment = as_pool.browse(cr, uid, assignment_ids[0])
            assignments[ticket['id']] = (assignment.id, assignment.user_id.name)
        return assignments

    def _set_assignment(self, cr, uid, ticket_id, name, value, fnct_inv_arg, context):
        """assign a ticket to a user for the current stage
        """
        if value is not False:
            ticket = self.browse(cr, uid, ticket_id, context)
            self.pool.get('anytracker.assignment').create(cr, uid, {
                'stage_id': ticket.stage_id.id,
                'ticket_id': ticket_id,
                'user_id': value,
                })

    _columns = {
        'assigned_user_id': fields.function(_get_assignment,
                                             fnct_inv=_set_assignment,
                                             type='many2one',
                                             relation='res.users',
                                             string="Last assigned user"),
        'assignment_ids': fields.one2many('anytracker.assignment', 'ticket_id', 'Assignments'),
    }
