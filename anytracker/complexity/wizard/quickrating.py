from odoo import models, fields, _
from odoo.exceptions import except_orm


class QuickRating(models.TransientModel):
    """Wizard for quick rating
    """
    _name = 'anytracker.quickrating'

    def next_ticket(self, ids, context=None):
        """React to the "Next" or "Previous" button
        """
        # save ticket data
        wizard = self.browse(ids, context)[0]
        ticket_data = {
            'description': wizard.description,
        }
        rating_id = wizard.my_rating
        if rating_id:
            ticket_data['my_rating'] = rating_id.id
        self.env('anytracker.ticket').write(
            [wizard.ticket_id.id],
            ticket_data)

        # go to next ticket
        ticket_vals = self.read(ids, ['ticket_id', 'ticket_ids'])[0]
        ticket_id, ticket_ids = ticket_vals['ticket_id'][0], eval(ticket_vals['ticket_ids'])
        position = ticket_ids.index(ticket_id)
        step = context.get('step')
        if step < 0 and position == 0:
            raise except_orm(_('Nothing before!'),
                             _('You are already on the first ticket.'))
        elif step > 0 and position == len(ticket_ids) - 1:
            return {'type': 'ir.actions.act_window_close'}
        position += context.get('step')
        next_ticket_id = ticket_ids[position]
        ticket = self.env('anytracker.ticket').browse(next_ticket_id)
        return self.write(ids,
                          {'ticket_id': next_ticket_id,
                           'method_id': ticket.project_id.method_id.id,
                           'my_rating': ticket.my_rating.id,
                           'progress': 100.0 * (position) / len(ticket_ids)
                           }, context)

    def _default_tickets(self, context=None):
        """select all tickets we will work on
        """
        ticket_pool = self.env('anytracker.ticket')
        ticket_ids = context.get('active_ids', [])
        ticket_id = context.get('active_id')
        # if one ticket selected, we take all the children
        if len(ticket_ids) == 1:
            ticket_id = context.get('active_ids')[0]
            ticket_ids = ticket_pool.search(
                [('id', 'child_of', ticket_id),
                 ('child_ids', '=', False)],
                context=context)
            tickets = ticket_pool.browse(ticket_ids, context)
            unrated_ticket_ids = [t.id for t in tickets if not t.my_rating]
            if unrated_ticket_ids:
                return str(sorted(unrated_ticket_ids))
        return str(sorted(ticket_ids))

    def _default_ticket(self, context=None):
        """select the first ticket we work on at wizard opening
        """
        ticket_id = eval(self._default_tickets(context))[0]
        return ticket_id

    def _default_breadcrumb(self, context=None):
        ticket_id = eval(self._default_tickets(context))[0]
        return self.pool.get('anytracker.ticket').browse(ticket_id).breadcrumb

    def _default_description(self, context=None):
        ticket_id = eval(self._default_tickets(context))[0]
        return self.pool.get('anytracker.ticket').browse(ticket_id).description

    def _default_method(self, context=None):
        ticket_id = eval(self._default_tickets(context))[0]
        ticket_obj = self.pool.get('anytracker.ticket')
        return ticket_obj.browse(ticket_id).project_id.method_id.id

    def _default_my_rating(self, context=None):
        ticket_id = eval(self._default_tickets(context))[0]
        return self.pool.get('anytracker.ticket').browse(ticket_id).my_rating.id

    ticket_id = fields.Many2one(
        'anytracker.ticket', 'Ticket',
        default=lambda self: self._default_ticket)
    ticket_ids = fields.Text(
        'Tickets to rate', default=lambda self: self._default_tickets)
    breadcrumb = fields.Char(
        'ticket_id.breadcrumb', readonly=True,
        default=lambda self: self._default_breadcrumb)
    description = fields.Text(
        'ticket_id.description',
        default=lambda self: self._default_description)
    method_id = fields.Many2one(
        'anytracker.method', 'Method',
        default=lambda self: self._default_method)
    my_rating = fields.Many2one(
        'anytracker.complexity', 'My rating',
        default=lambda self: self._default_my_rating)
    progress = fields.Float('Progress', default=0.0)
