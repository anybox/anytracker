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
        'stage_id': fields.many2one('anytracker.stage', 'Stage'),
        'date': fields.datetime('Date', help='Assignment date', required=True),
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }


class Ticket(osv.Model):
    """ Add assignment to tickets
    """
    _inherit = 'anytracker.ticket'

    def _get_assignment(self, cr, uid, ids, field_names, args, context=None):
        """ Return the latest assignment of the ticket for the current stage
        If the assignment stage is not the ticket stage, take an older one.
        """
        if not context:
            context = {}

        # Join in sql with a single request
        sql = ('SELECT t.id, t.stage_id, a.id, a.stage_id, a.user_id, u.user_email, a.date '
               'FROM anytracker_ticket t '
               'LEFT OUTER JOIN anytracker_assignment a '
               'ON t.id = a.ticket_id '
               'LEFT OUTER JOIN res_users u ON u.id = a.user_id '
               'WHERE t.id in %s '
               'ORDER BY date, t.id')
        cr.execute(sql, (tuple(ids),))
        ticket_assignments = cr.fetchall()
        assignments = {}
        # then process the result in a pure python loop, starting with the oldest
        for t_id, t_stage_id, a_id, a_stage_id, a_user_id, u_mail, a_date in ticket_assignments:
            assignment = {'assigned_user_id': a_user_id, 'assigned_user_email': u_mail}
            assignments[t_id] = assignment
            # to reenable the stage_id logic in assignment, replace the previous line with:
            #assignments.setdefault(t_id, assignment)
            # a more recent with the exact stage, or assignment without stage, keep it
            #if a_stage_id == t_stage_id or not a_stage_id:
            #    assignments[t_id] = assignment

        return assignments

    def _set_assignment(self, cr, uid, ticket_id, name, value, fnct_inv_arg, context):
        """assign a ticket to a user for the current stage
        """
        if value is not False:
            ticket = self.browse(cr, uid, ticket_id, context)
            self.pool.get('anytracker.assignment').create(
                cr, uid, {
                    'stage_id': ticket.stage_id.id,
                    'ticket_id': ticket_id,
                    'user_id': value,
                })

    def _search_assignment(self, cr, uid, obj, field, domain, context=None):
        """search on assigned_user_id.

        Return a domain for a search of tickets
        """
        req = ('select distinct a.ticket_id, a.date '
               'from anytracker_assignment a, anytracker_ticket t '
               'where a.user_id%s%s and a.stage_id = t.stage_id order by a.date desc')
        assert(len(domain) == 1 and len(domain[0]) == 3)  # handle just this case
        cr.execute(req % (domain[0][1], domain[0][2]))
        res = cr.fetchall()
        return [('id', 'in', [a[0] for a in res])]

    _columns = {
        'assigned_user_id': fields.function(
            _get_assignment,
            fnct_inv=_set_assignment,
            fnct_search=_search_assignment,
            type='many2one',
            relation='res.users',
            string="Assigned user",
            multi='assigned_user'),  # multi is the key to group function fields
        'assigned_user_email': fields.function(
            _get_assignment, type='string', multi='assigned_user', string='Assigned user email'),
        'assignment_ids': fields.one2many('anytracker.assignment', 'ticket_id',
                                          string="Stage assignments",
                                          help="Each time you assign a ticket to someone, "
                                          "the user and stage get recorded in this mapping. "
                                          "Later on, the assignment will change upon a stage "
                                          "change if and only if the new stage is found in "
                                          "this mapping. "
                                          "Only the most recent assignment for a given "
                                          "stage will be considered. Older ones are "
                                          "being displayed here for logging purposes only.",
                                          readonly=True),
    }

    def assign_to_current_user(self, cr, uid, record, context=None):
        """Assign the browse record to current user.

        Meant to be used in a server action of 'code' type.
        This could as well have been a 'write' action but
        - I don't have time to test these right now
        - we may want to do more than a simple write at some point
        """
        self.write(cr, uid, record.id, dict(assigned_user_id=uid))
