from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _


class QuickRating(osv.TransientModel):
    """Wizard for quick rating
    """
    _name = 'anytracker.quickrating'

    def next_ticket(self, cr, uid, ids, context=None):
        """React to the "Next" or "Previous" button
        """
        # save ticket data
        wizard = self.browse(cr, uid, ids, context)[0]
        ticket_data = {
            'description': wizard.description,
        }
        rating_id = wizard.my_rating
        if rating_id:
            ticket_data['my_rating'] = rating_id.id
        self.pool.get('anytracker.ticket').write(
            cr, uid,
            [wizard.ticket_id.id],
            ticket_data)

        # go to next ticket
        ticket_vals = self.read(cr, uid, ids, ['ticket_id', 'ticket_ids'])[0]
        ticket_id, ticket_ids = ticket_vals['ticket_id'][0], eval(ticket_vals['ticket_ids'])
        position = ticket_ids.index(ticket_id)
        step = context.get('step')
        if step < 0 and position == 0:
            raise osv.except_osv(_('Nothing before!'),
                                 _('You are already on the first ticket.'))
        elif step > 0 and position == len(ticket_ids) - 1:
            return {'type': 'ir.actions.act_window_close'}
        position += context.get('step')
        next_ticket_id = ticket_ids[position]
        ticket = self.pool.get('anytracker.ticket').browse(cr, uid, next_ticket_id)
        return self.write(cr, uid, ids,
                          {'ticket_id': next_ticket_id,
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
            ticket_ids = ticket_pool.search(
                cr, uid,
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

    def _default_breadcrumb(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).breadcrumb

    def _default_description(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).description

    def _default_method(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        ticket_obj = self.pool.get('anytracker.ticket')
        return ticket_obj.browse(cr, uid, ticket_id).project_id.method_id.id

    def _default_my_rating(self, cr, uid, context=None):
        ticket_id = eval(self._default_tickets(cr, uid, context))[0]
        return self.pool.get('anytracker.ticket').browse(cr, uid, ticket_id).my_rating.id

    _columns = {
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket'),
        'ticket_ids': fields.text('Tickets to rate'),
        'breadcrumb': fields.related(
            'ticket_id',
            'breadcrumb',
            type='char',
            string='Name',
            readonly=True),
        'description': fields.related(
            'ticket_id',
            'description',
            type='text',
            string='Description'),
        'method_id': fields.many2one('anytracker.method', 'Method'),
        'my_rating': fields.many2one('anytracker.complexity', 'My rating',),
        'progress': fields.float('Progress'),
    }

    _defaults = {
        'ticket_ids': _default_tickets,
        'ticket_id': _default_ticket,
        'breadcrumb': _default_breadcrumb,
        'description': _default_description,
        'method_id': _default_method,
        'progress': 0.0,
        'my_rating': _default_my_rating,
    }
