from osv import osv
from osv import fields
from tools.translate import _

class QuickRating(osv.TransientModel):
    """Wizard for quick rating
    """
    _name = 'anytracker.quickrating'

    def previous_ticket(self, cr, uid, ids, context=None):
        """React to the "Previous" button"""
        # save rating
        wizard = self.browse(cr, uid, ids, context)[0]
        rating_id = wizard.my_rating
        if rating_id:
            self.pool.get('anytracker.ticket').write(cr, uid, [wizard.ticket_id.id], {'my_rating': rating_id.id})

        # go to next ticket
        ticket_vals = self.read(cr, uid, ids, ['ticket_id', 'ticket_ids'])[0]
        ticket_id, ticket_ids = ticket_vals['ticket_id'][0], eval(ticket_vals['ticket_ids'])
        position = ticket_ids.index(ticket_id)
        if position == 0:
            raise osv.except_osv(_('Nothing before!'),_('You are already on the first ticket.'))
        position -= 1
        previous_ticket_id = ticket_ids[position]
        ticket = self.pool.get('anytracker.ticket').browse(cr, uid, previous_ticket_id)
        return self.write(cr, uid, ids, {'ticket_id': previous_ticket_id,
                                  'method_id': ticket.project_id.method_id.id,
                                  'my_rating': ticket.my_rating.id,
                                  'progress': 100.0 * (position) / len(ticket_ids)
                                 }, context)

    def next_ticket(self, cr, uid, ids, context=None):
        """React to the "Next" button"""
        # save rating
        wizard = self.browse(cr, uid, ids, context)[0]
        rating_id = wizard.my_rating
        if rating_id:
            self.pool.get('anytracker.ticket').write(cr, uid, [wizard.ticket_id.id], {'my_rating': rating_id.id})

        # go to next ticket
        ticket_vals = self.read(cr, uid, ids, ['ticket_id', 'ticket_ids'])[0]
        ticket_id, ticket_ids = ticket_vals['ticket_id'][0], eval(ticket_vals['ticket_ids'])
        position = ticket_ids.index(ticket_id)
        if position == len(ticket_ids) - 1:
            return {'type': 'ir.actions.act_window_close'}
        position += 1
        next_ticket_id = ticket_ids[position]
        ticket = self.pool.get('anytracker.ticket').browse(cr, uid, next_ticket_id)
        return self.write(cr, uid, ids, {'ticket_id': next_ticket_id,
                                  'method_id': ticket.project_id.method_id.id,
                                  'my_rating': ticket.my_rating.id,
                                  'progress': 100.0 * (position) / len(ticket_ids)
                                 }, context)

    def _default_tickets(self, cr, uid, context=None):
        """select all tickets we will work on
        """
        ticket_pool = self.pool.get('anytracker.ticket')
        ticket_ids = context.get('active_ids', [])
        ticket_id = context.get('active_id')
        # if one ticket selected, we take all the children
        if len(ticket_ids) == 1:
            ticket_id = context.get('active_ids')[0]
            ticket_ids = ticket_pool.search(cr, uid,
                [('id', 'child_of', ticket_id),
                 ('child_ids', '=', False)],
                context=context)
            tickets = ticket_pool.browse(cr, uid, ticket_ids, context)
            unrated_ticket_ids = [t.id for t in tickets if not t.my_rating]
            if unrated_ticket_ids:
                return str(sorted(unrated_ticket_ids))
        return str(sorted(ticket_ids))

    def _default_ticket(self, cr, uid, context=None):
        """select the first ticket we work on at wizard opening
        """
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return ticket_id

    def _default_name(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).name

    def _default_description(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).description

    def _default_method(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).project_method_id.id

    def _default_my_rating(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).my_rating.id

    _columns = {
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket'),
        'ticket_ids': fields.text('Tickets to rate'),
        'name': fields.related('ticket_id', 'name', type='char',
                            string='Name', readonly=True),
        'description': fields.related('ticket_id', 'description', type='text',
                            string='Description', readonly=True),
        'method_id': fields.many2one('anytracker.method', 'Method'),
        'my_rating': fields.many2one('anytracker.complexity', 'My rating',),
        'progress': fields.float('Progress'),
    }

    _defaults = {
        'ticket_ids': _default_tickets,
        'ticket_id': _default_ticket,
        'name': _default_name,
        'description': _default_description,
        'method_id': _default_method,
        'progress': 0.0,
        'my_rating': _default_my_rating,
    }
