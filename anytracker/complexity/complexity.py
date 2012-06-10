from osv import fields, osv
from tools.translate import _
import time


class complexity(osv.osv):
    """Definition of the different complexity levels, in different contexts.
    Example:
        - with a scrum method, values can be the fibonacci series
        - with a anytracker method, values are green, orange, red
        - ...
    """
    _name = 'anytracker.complexity'
    _columns = {
        'name': fields.char('Name', size=16, required=True),
        'value': fields.float('Value', required=True),
        'color': fields.integer('Color'),
        'method_id': fields.many2one('anytracker.method', 'Method', help='Projet method'),
    }


class rating(osv.osv):
    """Represents the rating of a ticket by one person at one time
    """
    _name = 'anytracker.rating'
    _order = 'time desc'
    _columns = {
        'complexity_id': fields.many2one('anytracker.complexity', 'Complexity'),
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket', required=True, ondelete="cascade"),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'time': fields.datetime('Date', required=True),
    }

class ticket(osv.osv):
    """Add complexity functionnality to tickets
    """
    _inherit = 'anytracker.ticket'

    def _get_my_rating(self, cr, uid, ids, field_name, args, context=None):
        """get my latest rating for this ticket
        """
        if not context: context = {}
        ar_pool = self.pool.get('anytracker.rating')
        tickets = {}
        for ticket_id in ids:
            tickets[ticket_id] = False
            rating_ids = ar_pool.search(cr, uid, 
                            [('user_id', '=', uid),
                             ('ticket_id', '=', ticket_id)],
                            context=context)
            if not rating_ids:
                continue
            rating = ar_pool.browse(cr, uid, rating_ids[0])
            if rating.complexity_id:
                my_rating = (rating.complexity_id.id, rating.complexity_id.name)
            else:
                my_rating = False
            tickets[ticket_id] = my_rating
        return tickets

    def _set_my_rating(self, cr, uid, id, name, value, fnct_inv_arg, context):
        """set my rating
        """
        self.pool.get('anytracker.rating').create(cr, uid, {
            'complexity_id': value,
            'ticket_id': id,
            'user_id': uid,
            'time': time.strftime('%Y-%m-%d %H:%M:%S')})

    def _get_color(self, cr, uid, ids, field_name, args, context=None):
        """get the color from my rating
        """
        if not context: context = {}
        tickets = {}
        for ticket in self.browse(cr, uid, ids, context):
            complexity = ticket.my_rating
            tickets[ticket.id] = getattr(complexity, 'color', False)
        return tickets

    _columns = { 
        'rating_ids': fields.one2many('anytracker.rating', 'ticket_id', 'Ratings'),
        'my_rating': fields.function(_get_my_rating,
                                     fnct_inv=_set_my_rating,
                                     type='many2one',
                                     domain="[('method_id','=',project_method_id)]",
                                     relation='anytracker.complexity',
                                     string="My Rating"),
        'color': fields.function(_get_color, type='integer', relation='anytracker.complexity', string='Color'),
     }
