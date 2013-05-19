# -*- coding: utf-8 -*-

from osv import osv
from osv import fields
import time


class Assignment(osv.Model):
    """ Several users can be assigned to a ticket at different stages
    So we have a separated object for assignment
    """
    _name = 'anytracker.assignment'
    _description = 'Stage assignments'
    _rec_name = 'user_id'
    _order = 'date DESC'

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=True),
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket', required=True),
        'stage_id': fields.many2one('anytracker.stage', 'Stage', required=True),
        'date': fields.datetime('Date', help='Assignment date', required=True),
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),  # TODO use a constant
    }


class Ticket(osv.Model):
    """ Add assignment to tickets
    """
    _inherit = 'anytracker.ticket'

    def _get_assignment(self, cr, uid, ids, field_names, args, context=None):
        """ Return the latest assignment of the ticket for the current stage
        """
        if not context:
            context = {}
        as_obj = self.pool.get('anytracker.assignment')
        assignments = {}

        default = dict((fid, False) for fid in field_names)

        def ass_search(domain, **kw):
            return as_obj.search(cr, uid, domain, order='date DESC', context=context, **kw)

        # TODO PERF rewrite this without browsing users inside of a loop
        # (at least a small cache if that's more readable than a direct read or SQL request)
        for ticket in self.read(cr, uid, ids, ['stage_id'], context):
            tid = ticket['id']
            assignments[tid] = default.copy()

            stage_id = ticket['stage_id']
            if not stage_id:
                continue
            stage_id = stage_id[0]
            stage_domain = ('stage_id', '=', stage_id)
            ticket_domain = ('ticket_id', '=', tid)

            assignment_ids = ass_search([ticket_domain, stage_domain], limit=1)
            if not assignment_ids:  # retry for any stage
                assignment_ids = ass_search([ticket_domain], limit=1)
                if not assignment_ids:
                    continue

            assignment = as_obj.browse(cr, uid, assignment_ids[0])

            assignments[tid] = dict(assigned_user_id=(assignment.id, assignment.user_id.name),
                                    assigned_user_email=(assignment.user_id.user_email))

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
