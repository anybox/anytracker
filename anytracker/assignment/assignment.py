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
        as_obj = self.pool.get('anytracker.assignment')
        assignments = {}
        for ticket in self.read(cr, uid, ids, ['stage_id'], context):
            assignments[ticket['id']] = False
            if not ticket['stage_id']: continue
            assignment_ids = as_obj.search(cr, uid,
                            [('stage_id', '=', ticket['stage_id'][0]),
                             ('ticket_id', '=', ticket['id'])],
                            context=context)
            if not assignment_ids:
                continue
            # assignments are ordered by 'date DESC' so we take the last
            assignment = as_obj.browse(cr, uid, assignment_ids[0])
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

    def _search_assignment(self, cr, uid, obj, field, domain, context=None):
        """search for assigned_user_id.
        Should return a domain for a search of tickets
        """
        req = ('select distinct a.ticket_id, a.date '
        'from anytracker_assignment a, anytracker_ticket t '
        'where a.user_id%s%s and a.stage_id = t.stage_id order by a.date desc')
        assert(len(domain)==1) # handle just this case
        assert(len(domain[0])==3) # handle just this case
        cr.execute(req % (domain[0][1], domain[0][2]))
        res = cr.fetchall()
        return [('id','in', [a[0] for a in res])]

    _columns = {
        'assigned_user_id': fields.function(_get_assignment,
                                             fnct_inv=_set_assignment,
                                             fnct_search=_search_assignment,
                                             type='many2one',
                                             relation='res.users',
                                             string="Last assigned user"),
        'assignment_ids': fields.one2many('anytracker.assignment', 'ticket_id', 'Assignments'),
    }
