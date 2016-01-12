# -*- coding: utf-8 -*-
from openerp import models, fields, api
import time


class Assignment(models.Model):
    """ Several users can be assigned to a ticket at different stages
    So we have a separated object for assignment
    """
    _name = 'anytracker.assignment'
    _description = 'Assignments'
    _rec_name = 'user_id'
    _order = 'date DESC'

    user_id = fields.Many2one(
        'res.users',
        string='User')
    ticket_id = fields.Many2one(
        'anytracker.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade')
    stage_id = fields.Many2one(
        'anytracker.stage',
        string='Stage',
        required=True)
    date = fields.Datetime(
        string='Date',
        default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        help='Assignment date',
        required=True)


class Ticket(models.Model):
    """ Add assignment to tickets
    """
    _inherit = 'anytracker.ticket'

    @api.depends('assignment_ids')
    def _get_assignment(self):
        """ Return the latest assignment of the ticket for the current stage
        If the assignment stage is not the ticket stage, take an older one.
        """
        if not self.ids:
            return
        # Join in sql with a single request
        sql = ('SELECT '
               't.id t_id, t.stage_id t_stage_id, a.id a_id, '
               'a.stage_id a_stage_id, a.user_id, p.email, a.date'
               ' FROM anytracker_ticket t'
               ' LEFT OUTER JOIN anytracker_assignment a ON t.id = a.ticket_id'
               ' LEFT OUTER JOIN res_users u ON u.id = a.user_id'
               ' LEFT OUTER JOIN res_partner p ON u.partner_id = p.id'
               ' WHERE t.id in %s'
               ' ORDER BY date, t.id')
        self.env.cr.execute(sql, (tuple(self.ids),))
        ticket_assignments = self.env.cr.dictfetchall()
        assigns = {}
        # then process the result in a pure python loop,
        # starting with the oldest
        for a in ticket_assignments:
            assignment = {
                'assigned_user_id': a['user_id'],
                'assigned_user_email': a['email']}
            assigns[a['t_id']] = assignment
            # to reenable the stage_id logic in assignment,
            # replace the previous line with:
            # assigns.setdefault(a['t_id'], assignment)
            # a more recent with the exact stage, or assignment without stage
            # (keep it)
            # if a['a_stage_id'] == a['t_stage_id'] or not ['a_stage_id']:
            #    assigns[a['t_id']] = assignment

        for ticket in self:
            assign = assigns.get(ticket.id)
            if assign:
                ticket.assigned_user_id = assign['assigned_user_id']
                ticket.assigned_user_email = assign['assigned_user_email']

    def _set_assignment(self):
        """assign a ticket to a user for the current stage
        """
        ASSIGNMENT = self.env['anytracker.assignment']
        for ticket in self:
            # stage_id = (ticket.stage_id.id
            #             or ticket.with_context({
            #                 'active_id': ticket.id})._default_stage())
            new_id = ASSIGNMENT.create({
                # 'stage_id': stage_id,
                'ticket_id': ticket.id,
                'user_id': ticket.assigned_user_id.id,
            })
            ticket.assignment = new_id.id

    assigned_user_id = fields.Many2one(
        'res.users',
        compute='_get_assignment',
        inverse='_set_assignment',
        string="Assigned user",
        store=True)
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

    def assign_to_me(self):
        """Assign the ticket_id and sub-tickets to current user.
        """
        for ticket in self:
            ticket.write({'assigned_user_id': self.env.user.id})
