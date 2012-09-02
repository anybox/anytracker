from osv import fields, osv
import time


class Complexity(osv.Model):
    """Definition of the different complexity levels, in different contexts.
    Example:
        - with a 'scrum' method, values can be the fibonacci series
        - with an 'implementation' method, values are green, orange, red
        - ...
    """
    _name = 'anytracker.complexity'
    _columns = {
        'name': fields.char('Name', size=16, required=True),
        'description': fields.text('Description', help='Description of this complexity'),
        'value': fields.float('Value', required=True),
        'color': fields.integer('Color'),
        'method_id': fields.many2one('anytracker.method', 'Project method', help='Projet method'),
        'risk': fields.float('Risk', required=True,
            help="risk is a value between 0 (no risk) and 100 (full risk)"),
    }


class Rating(osv.Model):
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

class Ticket(osv.Model):
    """Add complexity and risk functionnality to tickets
    Risk is based on complexities. Each complexity has a risk value,
    and the risk is copied on the ticket
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
        if value is not False:
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

    def compute_risk(self, cr, uid, ids, context=None):
        """compute the risk of a leaf ticket, given its ratings
        """
        res = {}
        if type(ids) is int: ids = [ids]
        for ticket in self.browse(cr, uid, ids, context):
            if ticket.child_ids: # not a leaf
                res[ticket.id] = ticket.risk
                continue
            latest_person_ratings = {}
            # find latest rating for each person
            relevant_ratings = sorted([(r.time, r.user_id, r.complexity_id.risk) for r in ticket.rating_ids])
            for rating in relevant_ratings:
                latest_person_ratings[rating[1]] = rating[2]
            # compute the mean of all latest ratings
            risk_mean = sum(latest_person_ratings.values())/len(latest_person_ratings) if latest_person_ratings else 100.0
            res[ticket.id] = risk_mean
        return res

    def write(self, cr, uid, ids, values, context=None):
        """Climb the tree from the ticket to the root
        and recompute the risk of parents
        Unrated tickets have a risk of 100.0!!
        """
        if type(ids) is int: ids = [ids]
        if 'my_rating' in values:
            old_risk = self.compute_risk(cr, uid, ids, context)

        res = super(Ticket, self).write(cr, uid, ids, values, context)

        if 'my_rating' not in values:
            return res
        for ticket in self.browse(cr, uid, ids, context):
            new_risk = self.compute_risk(cr, uid, [ticket.id], context)[ticket.id]
            ticket.write({'risk': new_risk})
            parent = ticket.parent_id
            #loop up to the root
            while parent:
                child_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                                  ('child_ids', '=', False),
                                                  ('id', '!=', parent.id)])
                risk_increase = (ticket.risk - old_risk[ticket.id])/len(child_ids)
                new_risk = parent.risk + risk_increase
                new_risk = 100.0 if new_risk > 100.0 else new_risk
                new_risk = 0.0 if new_risk < 0.0 else new_risk
                parent.write({'risk': new_risk})
                parent = parent.parent_id
        return res


    _columns = { 
        'rating_ids': fields.one2many('anytracker.rating', 'ticket_id', 'Ratings'),
        'my_rating': fields.function(_get_my_rating,
                                     fnct_inv=_set_my_rating,
                                     type='many2one',
                                     domain="[('method_id','=',method_id)]",
                                     relation='anytracker.complexity',
                                     string="My Rating"),
        'risk': fields.float('Risk'),
        'color': fields.function(_get_color, type='integer', relation='anytracker.complexity', string='Color'),
     }

    _defaults = {
        'risk': 100.0,
    }
