# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
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
        'user_id': fields.many2one('res.users', 'User'),
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket',
                                     required=True, ondelete='cascade'),
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

    def _ids_to_recompute(self, cr, uid, ids, context=None):
        """ return list of tickets ids that need to be recompute """
        res = []
        for assignment_id in self.browse(cr, uid, ids):
            res.append(assignment_id.ticket_id.id)
        return res

    def _get_assignment(self, cr, uid, ids, field_names, args, context=None):
        """ Return the latest assignment of the ticket for the current stage
        If the assignment stage is not the ticket stage, take an older one.
        """
        if not ids:
            return False
        if not context:
            context = {}

        # Join in sql with a single request
        sql = ('SELECT t.id, t.stage_id, a.id, a.stage_id, a.user_id, p.email, a.date '
               'FROM anytracker_ticket t '
               'LEFT OUTER JOIN anytracker_assignment a ON t.id = a.ticket_id '
               'LEFT OUTER JOIN res_users u ON u.id = a.user_id '
               'LEFT OUTER JOIN res_partner p ON u.partner_id = p.id '
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
            # assignments.setdefault(t_id, assignment)
            # a more recent with the exact stage, or assignment without stage, keep it
            # if a_stage_id == t_stage_id or not a_stage_id:
            #    assignments[t_id] = assignment

        return assignments

    def _set_assignment(self, cr, uid, ticket_id, name, value, fnct_inv_arg, context):
        """assign a ticket to a user for the current stage
        """
        ticket = self.browse(cr, uid, ticket_id, context)
        stage_id = (ticket.stage_id.id
                    or self._default_stage(cr, uid, context={'active_id': ticket_id}))
        self.pool.get('anytracker.assignment').create(cr, uid, {
            'stage_id': stage_id,
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
            store={'anytracker.assignment': (_ids_to_recompute, ['user_id'], 10)},
            multi='assigned_user'),  # multi is the key to group function fields
        'assigned_user_email': fields.function(
            _get_assignment,
            type='char',
            multi='assigned_user',
            string='Assigned user email'),
        'assignment_ids': fields.one2many(
            'anytracker.assignment', 'ticket_id',
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

    def assign_to_me(self, cr, uid, ids, context=None):
        """Assign the ticket_id and sub-tickets to current user.
        """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for ticket_id in ids:
            subtickets_ids = self.search(cr, uid, [('id', 'child_of', ticket_id)])
            # subtickets_ids.remove(ticket_id)
            # subtickets_ids.append(ticket_id)
            self.write(cr, uid, subtickets_ids, dict(assigned_user_id=uid))
