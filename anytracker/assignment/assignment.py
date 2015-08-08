# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import time


class Assignment(models.Model):
    """ Several users can be assigned to a ticket at different stages
    So we have a separated object for assignment
    """
    _name = 'anytracker.assignment'
    _description = 'Assignments'
    _rec_name = 'user_id'
    _order = 'date DESC'

    user_id = fields.Many2one('res.users', string='User')
    ticket_id = fields.Many2one('anytracker.ticket', string='Ticket',
                                required=True, ondelete='cascade')
    stage_id = fields.Many2many('anytracker.stage', 'assignment_stage_rel', 'assignment_id', 'stage_id', string='Stage')
    date = fields.Datetime(string='Date', help='Assignment date', required=True)

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }


class Ticket(models.Model):
    """ Add assignment to tickets
    """
    _inherit = 'anytracker.ticket'

    def _ids_to_recompute(self, cr, uid, ids, context=None):
        """ return list of tickets ids that need to be recompute """
        res = []
        for assignment_id in self.browse(cr, uid, ids):
            res.append(assignment_id.ticket_id.id)
        return res

    @api.one
    @api.depends('assignment_ids.user_id')
    def _get_assignment(self):
        if self.ids:
            """ Return the latest assignment of the ticket for the current stage
            If the assignment stage is not the ticket stage, take an older one.
            """
            # Join in sql with a single request
            assignment_ids = self.env['anytracker.assignment'].search([('id', '=', self.ids)])
            if assignment_ids:
                self.assigned_user_email = assignment_ids[0].user_id.email
                self.assigned_user_id = assignment_ids[0].user_id.id

            self.stage_id
            sql = ('SELECT t.id, t.stage_id, a.id, a.stage_id, a.user_id, p.email, a.date '
                   'FROM anytracker_ticket t '
                   'LEFT OUTER JOIN anytracker_assignment a ON t.id = a.ticket_id '
                   'LEFT OUTER JOIN res_users u ON u.id = a.user_id '
                   'LEFT OUTER JOIN res_partner p ON u.partner_id = p.id '
                   'WHERE t.id in %s '
                   'ORDER BY date, t.id')
            # self._cr.execute(sql, (tuple([self.id]),))
            # ticket_assignments = self._cr.fetchall()
            assignments = {}
            # then process the result in a pure python loop, starting with the oldest
            # for t_id, t_stage_id, a_id, a_stage_id, a_user_id, u_mail, a_date in ticket_assignments:
            #     assignment = {'assigned_user_id': a_user_id, 'assigned_user_email': u_mail}
            #     self.assigned_user_email = u_mail
            #     self.assigned_user_id = a_user_id
                # assignments[t_id] = assignment
                # to reenable the stage_id logic in assignment, replace the previous line with:
                # assignments.setdefault(t_id, assignment)
                # a more recent with the exact stage, or assignment without stage, keep it
                # if a_stage_id == t_stage_id or not a_stage_id:
                #    assignments[t_id] = assignment

                # return assignments

    @api.one
    def _set_assignment(self):
        """assign a ticket to a user for the current stage
        """
        stage_id = (self.stage_id.id
                    or self._default_stage(context={'active_id': self.ids}))
        new_id = self.env['anytracker.assignment'].create({
            'stage_id': stage_id,
            'ticket_id': self.ids[0],
            # 'user_id':1,
        })
        self.assigned_user_id = new_id

    assigned_user_id = fields.Many2one(
        'res.users',
        compute='_get_assignment',
        # inverse=_set_assignment,
        string="Assigned user",
        # store={'anytracker.assignment': (_ids_to_recompute, ['user_id'], 10)},
        # multi='assigned_user'
    )  # multi is the key to group function fields
    assigned_user_email = fields.Char(
        compute='_get_assignment',
        # multi='assigned_user',
        string='Assigned user email')
    assignment_ids = fields.One2many(
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
        readonly=True)

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
