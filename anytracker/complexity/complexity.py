from openerp.osv import osv
from openerp.osv import fields
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
        'name': fields.char('Name', size=64, required=True, translate=True),
        'description': fields.text(
            'Description', help='Description of this complexity', translate=True),
        'value': fields.float('Value', required=True),
        'color': fields.integer('Color'),
        'method_id': fields.many2one('anytracker.method', 'Project method',
                                     help='Projet method', ondelete='cascade'),
        'risk': fields.float(
            'Risk', required=True,
            help="risk is a value between 0.0 (no risk) and 1.0 (full risk)"),
    }


class Rating(osv.Model):
    """Represents the rating of a ticket by one person at one time
    """
    _name = 'anytracker.rating'
    _order = 'time desc'
    _columns = {
        'complexity_id': fields.many2one('anytracker.complexity', 'Complexity'),
        'ticket_id': fields.many2one(
            'anytracker.ticket', 'Ticket', required=True, ondelete="cascade"),
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
        if not context:
            context = {}
        ar_pool = self.pool.get('anytracker.rating')
        ratings = {}
        for ticket_id in ids:
            ratings[ticket_id] = False
            rating_ids = ar_pool.search(
                cr, uid,
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
            ratings[ticket_id] = my_rating
        return ratings

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
        if not context:
            context = {}
        tickets = {}
        for ticket in self.browse(cr, uid, ids, context):
            complexity = ticket.my_rating
            tickets[ticket.id] = getattr(complexity, 'color', False)
        return tickets

    def compute_risk_and_rating(self, cr, uid, ids, context=None):
        """compute the risk and rating of a leaf ticket, given all its individual ratings
        """
        res_risk, res_rating = {}, {}
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for ticket in self.browse(cr, uid, ids, context):
            if ticket.child_ids:  # not a leaf
                res_risk[ticket.id] = ticket.risk
                res_rating[ticket.id] = ticket.rating
                continue
            latest_person_risk, latest_person_rating = {}, {}
            # find latest risk and rating for each person
            for rating in sorted([(r.time, r.user_id, r.complexity_id.risk)
                                  for r in ticket.rating_ids]):
                latest_person_risk[rating[1]] = rating[2]
            for rating in sorted([(r.time, r.user_id, r.complexity_id.value)
                                  for r in ticket.rating_ids]):
                latest_person_rating[rating[1]] = rating[2]
            # compute the mean of all latest ratings
            risk_mean = (sum([r or 0.5
                             for r in latest_person_risk.values()]
                             )/len(latest_person_risk)
                         if latest_person_risk else 0.5)
            rating_mean = (sum([r or 0.0 for r in
                               latest_person_rating.values()]
                               )/len(latest_person_rating)
                           if latest_person_rating else 0)
            res_risk[ticket.id] = risk_mean
            res_rating[ticket.id] = rating_mean
        return res_risk, res_rating

    def recompute_subtickets(self, cr, uid, ids, context=None):
        """recompute the overall risk and rating of the node, based on subtickets.
        And recompute sub-nodes as well
        """
        if not context:
            context = {}
        for ticket in self.browse(cr, uid, ids, context):
            if not ticket.child_ids:
                risk, rating = self.compute_risk_and_rating(cr, uid, ticket.id, context)
                self.write(cr, uid, ticket.id, {'risk': risk[ticket.id],
                                                'rating': rating[ticket.id]}, context)
            else:
                leaf_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                 ('child_ids', '=', False),
                                                 ('id', '!=', ticket.id)])
                self.recompute_subtickets(cr, uid, leaf_ids, context)

                sub_node_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                     ('child_ids', '!=', False),
                                                     ('id', '!=', ticket.id)])
                for node_id in [ticket.id] + sub_node_ids:
                    leaf_ids = self.search(cr, uid, [('id', 'child_of', node_id),
                                                     ('child_ids', '=', False),
                                                     ('id', '!=', node_id)])
                    reads = self.read(cr, uid, leaf_ids, ['risk', 'rating'], context)
                    ratings = [r['rating'] for r in reads]
                    rating = sum(ratings)
                    risks = [r['risk'] for r in reads]
                    risk = 1 - reduce(lambda x, y: x*y, [(1-r) for r in risks])**(1./len(risks))
                    self.write(cr, uid, node_id, {'risk': risk, 'rating': rating}, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        project_ids = self.read(cr, uid, ids, ['project_id'], load='_classic_write')
        super(Ticket, self).unlink(cr, uid, ids, context)
        self.recompute_subtickets(cr, uid, [v['project_id'] for v in project_ids])

    def write(self, cr, uid, ids, values, context=None):
        """Climb the tree from the ticket to the root
        and recompute the risk of parents
        Unrated tickets have a risk of 0.5 and rating of 0.0!!
        """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        if 'my_rating' in values or 'parent_id' in values:
            old_values = {v['id']: v for v in
                          self.read(cr, uid, ids, ['risk', 'rating', 'parent_id', 'project_id'],
                          context, load='_classic_write')}
            old_parents = {v['id']: v['parent_id'] for v in old_values.values()}
        res = super(Ticket, self).write(cr, uid, ids, values, context)
        if 'my_rating' in values or 'parent_id' in values:
            # update the rating and risk (which may be different for each ticket,
            # even if my_rating is the same)
            new_risk, new_rating = self.compute_risk_and_rating(cr, uid, ids)
            for ticket_id in ids:
                super(Ticket, self).write(cr, uid, ticket_id,
                                          {'risk': new_risk[ticket_id],
                                           'rating': new_rating[ticket_id]}, context)
        # Propagate to the parents
        if 'my_rating' in values and 'parent_id' not in values:
            self.recompute_parents(cr, uid, ids, old_values, old_parents)
        elif 'parent_id' in values and values['parent_id']:
            # We reparented, we recompute the subnodes
            old_projects = [v['project_id'] for v in old_values.values()]
            new_projects = [v['project_id'] for v in
                            self.read(cr, uid, ids, ['project_id'], load='_classic_write')]
            self.recompute_subtickets(cr, uid, list(set(old_projects + new_projects)))
        return res

    def create(self, cr, uid, values, context=None):
        """climb the tree up to the root and recompute
        """
        ticket_id = super(Ticket, self).create(cr, uid, values, context)
        parent_ids = {ticket_id: values.get('parent_id')}
        self.recompute_parents(cr, uid, [ticket_id], None, parent_ids, nb=+1)
        return ticket_id

    def recompute_parents(self, cr, uid, ids, old_values, parent_ids, nb=0):
        """climb the tree starting from parent_ids up to the root
        and recompute the risk and rating of the parents, using:
          * old_values is the values of the tickets before change or moving
          * nb is -1 if the ticket was removed, 1 is added, or 0 if just changed

        If we have 3 tickets with risks a, b, c, we compute the overall risk as:
            R3 = 1 - ((1-a)(1-b)-(1-c))^1/3
        If we had n tickets and we create a new ticket with risk rn, the new risk Rn is:
            Rn = 1-((1-rn)(1-Rn)^n)^(1/(n+1))
        If we had n tickets and we delete a ticket, the new risk is:
            Rn = 1-(((1-Rn)^n)/(1-rn))^(1/(n-1))
        If we increase the risk of a ticket by x, the new risk is:
            Rn' = 1-(1-Rn)(1-x/(1-rn))**(1/n)
        """
        # ticket is the ticket that has been changed or reparented
        for ticket in self.browse(cr, uid, ids):
            if not parent_ids[ticket.id]:
                continue
            # parent is the parent to recompute (may be old or new)
            parent = self.browse(cr, uid, parent_ids[ticket.id])
            # loop up to the root
            while parent:
                child_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                                  ('child_ids', '=', False),
                                                  ('id', '!=', parent.id)])
                if nb == 0:  # we did not reparent
                    # rating
                    rating_increase = ticket.rating - old_values[ticket.id]['rating']
                    new_rating = parent.rating + rating_increase
                    # risk
                    old_risk = old_values[ticket.id]['risk']
                    risk_increase = ticket.risk - old_risk
                    n = len(child_ids)
                    new_risk = 1 - (1-parent.risk)*(1-risk_increase/(1-old_risk))**(1./n)
                    parent.write({'risk': new_risk, 'rating': new_rating})
                elif nb == 1:  # we added a ticket
                    # rating
                    rating_increase = ticket.rating
                    new_rating = parent.rating + rating_increase
                    # risk
                    n = len(child_ids) - 1
                    new_risk = 1 - ((1-ticket.risk)*(1-parent.risk)**n)**(1./(n+1))
                    if n == 0:  # The parent was a ticket (not a node)
                        new_risk = ticket.risk
                    parent.write({'risk': new_risk, 'rating': new_rating})
                else:
                    raise NotImplementedError('Bad value for nb')

                parent = parent.parent_id

    _columns = {
        'rating_ids': fields.one2many('anytracker.rating', 'ticket_id', 'Ratings'),
        'my_rating': fields.function(
            _get_my_rating, fnct_inv=_set_my_rating, type='many2one',
            relation='anytracker.complexity',
            string="My Rating"),
        'risk': fields.float('Risk', group_operator="avg",),
        'color': fields.function(
            _get_color, type='integer',
            relation='anytracker.complexity',
            string='Color'),
        'rating': fields.float('Rating', group_operator="sum",),
    }

    _defaults = {
        'risk': 0.5,
    }


class Method(osv.Model):
    _inherit = 'anytracker.method'
    _columns = {
        'complexity_ids': fields.one2many(
            'anytracker.complexity',
            'method_id',
            'Complexities',
            help="The complexities associated to this method"),
    }
