from openerp.osv import osv
from openerp.osv import fields
import time


def risk_mean(risks):
    risks = [(1-r) for r in risks if r is not None]
    if len(risks) == 0:
        return 0.5
    return 1 - reduce(lambda x, y: x*y, risks)**(1./len(risks))


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

    _sql_constraint = [
        ('value_uniq', 'unique(method_id, value)', 'Value must be different from others')]


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
                order='time DESC, id DESC',
                context=context)
            if not rating_ids:
                continue
            rating = ar_pool.browse(cr, uid, rating_ids[0])
            if rating.complexity_id:
                ratings[ticket_id] = (rating.complexity_id.id, rating.complexity_id.name)
        return ratings

    def _set_my_rating(self, cr, uid, ticket_id, name, value, fnct_inv_arg, context):
        """set my rating
        """
        if value is not False:
            self.pool.get('anytracker.rating').create(cr, uid, {
                'complexity_id': value,
                'ticket_id': ticket_id,
                'user_id': uid,
                'time': time.strftime('%Y-%m-%d %H:%M:%S')})

    def _get_color(self, cr, uid, ids, field_name, args, context=None):
        """get the color of the rating with highest risk
        """
        if not context:
            context = {}
        tickets = {}
        for ticket in self.browse(cr, uid, ids, context):
            colors = list(((r.complexity_id.risk, r.complexity_id) for r in ticket.rating_ids))
            if colors:
                tickets[ticket.id] = list(reversed(sorted(colors)))[0][1].color
            else:
                tickets[ticket.id] = 0
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
            for rating in sorted([(r.time, r.id, r.user_id, r.complexity_id.risk)
                                  for r in ticket.rating_ids]):
                latest_person_risk[rating[2]] = rating[-1]
            for rating in sorted([(r.time, r.id, r.user_id, r.complexity_id.value)
                                  for r in ticket.rating_ids]):
                latest_person_rating[rating[2]] = rating[-1]
            # a rating or risk of False or None is skipped
            latest_person_rating = dict([r for r in latest_person_rating.items()
                                         if r[-1] not in (None, False)])
            latest_person_risk = dict([r for r in latest_person_risk.items()
                                       if r[-1] not in (None, False)])
            # compute the mean of all latest ratings
            res_risk[ticket.id] = (risk_mean(latest_person_risk.values())
                                   if latest_person_risk else 0.5)
            res_rating[ticket.id] = (sum(latest_person_rating.values()
                                         )/len(latest_person_rating)
                                     if latest_person_rating else 0)
        return res_risk, res_rating

    def recompute_subtickets(self, cr, uid, ids, context=None):
        """recompute the overall risk and rating of the node, based on subtickets.
        And recompute sub-nodes as well
        """
        if not ids:
            return
        for ticket in self.browse(cr, uid, ids):
            if not ticket.child_ids:
                risk, rating = self.compute_risk_and_rating(cr, uid, ticket.id)
                self.write(cr, uid, ticket.id, {'risk': risk[ticket.id],
                                                'rating': rating[ticket.id]})
            else:
                leaf_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                 ('child_ids', '=', False),
                                                 ('id', '!=', ticket.id)])
                self.recompute_subtickets(cr, uid, leaf_ids)

                sub_node_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                     ('child_ids', '!=', False),
                                                     ('id', '!=', ticket.id)])
                for node_id in [ticket.id] + sub_node_ids:
                    leaf_ids = self.search(cr, uid, [('id', 'child_of', node_id),
                                                     ('child_ids', '=', False),
                                                     ('id', '!=', node_id)])
                    reads = self.read(cr, uid, leaf_ids, ['risk', 'rating'])
                    ratings = [r['rating'] for r in reads]
                    rating = sum(ratings)
                    risks = [r['risk'] for r in reads]
                    risk = risk_mean(risks)
                    self.write(cr, uid, node_id, {'risk': risk, 'rating': rating})
        return True

    def unlink(self, cr, uid, ids, context=None):
        tickets = self.read(cr, uid, ids, ['parent_id'], load='_classic_write')
        for ticket in tickets:
            # check if the old parent had other children
            children = self.read(cr, uid, ticket['parent_id'], ['child_ids'])
            if len(children['child_ids']) == 1:
                self.write(cr, uid, ticket['parent_id'], {'rating': 0.0, 'risk': 0.5})
        super(Ticket, self).unlink(cr, uid, ids, context)
        # recompute the remaining
        remaining = self.search(cr, uid, [('id', 'in', [v['parent_id'] for v in tickets])])
        self.recompute_parents(cr, uid, remaining)

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
            old_parents = [v['parent_id'] for v in old_values.values()]
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
            self.recompute_parents(cr, uid, old_parents)
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
        if values.get('parent_id'):
            self.recompute_parents(cr, uid, values.get('parent_id'))
        return ticket_id

    def recompute_parents(self, cr, uid, ids):
        """climb the tree starting from ids up to the root
        and recompute the risk and rating of each ticket.

        The overall rating is the sum of all the rating below.
        If we have 3 tickets with risks a, b, c, we compute the overall risk as:
            R3 = 1 - ((1-a)(1-b)-(1-c))^1/3
        """
        # ticket is the ticket that has been changed or reparented
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        if not ids:
            return
        for ticket in self.browse(cr, uid, ids):
            parent = ticket if ticket else None
            if not parent:
                continue
            # loop up to the root
            while parent:
                leaf_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                                 ('child_ids', '=', False),
                                                 ('id', '!=', parent.id)])
                if leaf_ids:
                    reads = self.read(cr, uid, leaf_ids, ['rating', 'risk'], load='_classic_write')
                    # rating
                    rating = sum(r['rating'] for r in reads)
                    # risk
                    risks = [r['risk'] for r in reads]
                    risk = risk_mean(risks)
                    self.write(cr, uid, parent.id, {'risk': risk, 'rating': rating})
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

    def copy(self, cr, uid, method_id, default, context=None):
        """ Customize the method copy
        """
        stages = self.pool.get('anytracker.stage')
        new_method_id = super(Method, self).copy(cr, uid, method_id, default, context)
        # update forbidden complexities for new stages
        for old_stage in self.browse(cr, uid, method_id).stage_ids:
            new_stage_ids = stages.search(cr, uid, [('state', '=', old_stage.state),
                                                    ('method_id', '=', new_method_id)])
            if new_stage_ids:
                new_stage = stages.browse(cr, uid, new_stage_ids[0])
                # link to the equivalent forbidden complexities
                old_cmplx_ids = [c.value for c in old_stage.forbidden_complexity_ids]
                if not old_cmplx_ids:
                    continue
                equ_cmplx_ids = self.pool.get('anytracker.complexity').search(
                    cr, uid, [('value', 'in', old_cmplx_ids),
                              ('method_id', '=', new_stage.method_id.id)])
                new_stage.write({'forbidden_complexity_ids': [(6, 0, equ_cmplx_ids)]})
        return new_method_id
