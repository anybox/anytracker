from openerp import models, fields, api
from datetime import datetime
from itertools import groupby


def risk_mean(risks):
    risks = [(1 - r) for r in risks if r is not None]

    if len(risks) == 0:
        return 0.5
    return 1 - reduce(lambda x, y: x * y, risks) ** (1. / len(risks))


class Complexity(models.Model):
    """Definition of the different complexity levels, in different contexts.
    Example:
        - with a 'scrum' method, values can be the fibonacci series
        - with an 'implementation' method, values are green, orange, red
        - ...
    """
    _name = 'anytracker.complexity'

    name = fields.Char(
        'Name',
        size=64,
        required=True,
        translate=True)
    description = fields.Text(
        'Description',
        help='Description of this complexity',
        translate=True)
    value = fields.Float(
        'Value',
        required=True)
    color = fields.Char(
        "Color",
        help="Color (in any CSS format) used to represent this complexity")
    method_id = fields.Many2one(
        'anytracker.method',
        'Project method',
        help='Projet method',
        ondelete='cascade')
    risk = fields.Float(
        'Risk', required=True,
        help="risk is a value between 0.0 (no risk) and 1.0 (full risk)")


class Rating(models.Model):
    """Represents the rating of a ticket by one person at one time
    """
    _name = 'anytracker.rating'
    _order = 'time DESC'

    complexity_id = fields.Many2one(
        'anytracker.complexity',
        'Complexity')
    ticket_id = fields.Many2one(
        'anytracker.ticket',
        'Ticket',
        required=True,
        ondelete="cascade")
    user_id = fields.Many2one(
        'res.users',
        'User',
        required=True)
    time = fields.Datetime(
        'Date',
        required=True)


class Ticket(models.Model):
    """Add complexity and risk functionnality to tickets
    Risk is based on complexities. Each complexity has a risk value,
    and the risk is copied on the ticket
    """
    _inherit = 'anytracker.ticket'

    @api.depends('rating_ids', 'parent_id', 'child_ids')
    def _get_my_rating(self):
        """get my latest rating for this ticket
        """
        RATING = self.env['anytracker.rating']
        rating = False
        for ticket in self:
            ratings = RATING.search(
                [('user_id', '=', ticket.env.uid),
                 ('ticket_id', '=', ticket.id)],
                order='time DESC, id DESC')
            if ratings:
                rating = ratings[0].complexity_id.id
            ticket.my_rating = rating

    def _set_my_rating(self):
        """set my rating
        """
        # pre-read ratings of the recordset because I found a cache bug
        # if I replace ratings[ticket.id] with ticket.my_rating.id
        ratings = {t.id: t.my_rating.id for t in self}
        RATING = self.env['anytracker.rating']
        for ticket in self:
            RATING.create({
                'complexity_id': ratings[ticket.id],
                'ticket_id': ticket.id,
                'user_id': ticket.env.uid,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')})

    @api.depends('rating_ids', 'my_rating', 'parent_id',
                 'child_ids', 'highest_rating')
    def _color(self):
        """get the color of the rating with highest risk
        """
        for ticket in self:
            if ticket.highest_rating:
                ticket.color = ticket.highest_rating.color
            else:
                ticket.color = 'white'

    @api.depends('rating_ids', 'my_rating', 'parent_id', 'child_ids')
    def _highest_rating(self):
        """get the rating of the highest risk of each person's latest rating
        """
        for ticket in self:
            ratings = list((r.user_id, r.complexity_id.value, r.complexity_id)
                           for r in ticket.sudo().rating_ids)
            if ratings:
                # group by user
                grouped = groupby(ratings, lambda x: x[0])
                # keep the latest of each user
                latests = [j[1].next() for j in grouped]
                # keep the highest
                highests = list(reversed(sorted(latests, key=lambda x: x[1])))
                if highests:
                    ticket.highest_rating = highests[0][2]

    def compute_risk_and_rating(self, ids):
        """compute the risk and rating of a leaf ticket,
        given all its individual ratings
        """
        # TODO: split risk and rating
        res_risk, res_rating = {}, {}
        for ticket in self.browse(ids):
            if ticket.type.has_children:  # not a leaf
                res_risk[ticket.id] = ticket.risk
                res_rating[ticket.id] = ticket.rating
                continue
            latest_person_risk, latest_person_rating = {}, {}
            # find latest risk and rating for each person
            for risk in sorted([(r.time, r.id, r.user_id, r.complexity_id.risk)
                                for r in ticket.rating_ids]):
                latest_person_risk[risk[2]] = risk[-1]
            for rating in sorted(
                [(r.time, r.id, r.user_id, r.complexity_id.value)
                 for r in ticket.rating_ids]):
                latest_person_rating[rating[2]] = rating[-1]
            # a rating or risk of False or None is skipped
            latest_person_rating = dict(
                [r for r in latest_person_rating.items()
                 if r[-1] not in (None, False)])
            latest_person_risk = dict(
                [r for r in latest_person_risk.items()
                 if r[-1] not in (None, False)])
            # compute the mean of all latest ratings
            res_risk[ticket.id] = (risk_mean(latest_person_risk.values())
                                   if latest_person_risk else 0.5)
            res_rating[ticket.id] = (sum(latest_person_rating.values()
                                         ) / len(latest_person_rating)
                                     if latest_person_rating else 0)
        return res_risk, res_rating

    def recompute_subtickets(self):
        """recompute the overall risk and rating of the node, based on subtickets.
        And recompute sub-nodes as well
        """
        for ticket in self:
            if not ticket.type.has_children:
                risk, rating = self.compute_risk_and_rating(ticket.id)
                ticket.write({'risk': risk[ticket.id],
                              'rating': rating[ticket.id]})
            else:
                leafs = self.search([('id', 'child_of', ticket.id),
                                     ('type.has_children', '=', False),
                                     ('id', '!=', ticket.id)])
                leafs.recompute_subtickets()

                subnodes = self.search([('id', 'child_of', ticket.id),
                                        ('type.has_children', '=', True),
                                        ('id', '!=', ticket.id)])
                for node in ticket + subnodes:
                    leafs = self.search([('id', 'child_of', node.id),
                                         ('type.has_children', '=', False),
                                         ('id', '!=', node.id)])
                    rating = sum(leaf.rating for leaf in leafs)
                    risk = risk_mean(leaf.risk for leaf in leafs)
                    node.write({'risk': risk, 'rating': rating})
        return True

    @api.multi
    def unlink(self):
        parent_ids = self.parent_id.ids
        for ticket in self:
            # check if the old parent had other children
            if len(ticket.parent_id.child_ids) == 1:
                ticket.parent_id.write({'rating': 0.0, 'risk': 0.5})
        super(Ticket, self).unlink()
        # recompute the remaining
        self.search([('id', 'in', parent_ids)]).recompute_parents()

    def write(self, values):
        """Climb the tree from the ticket to the root
        and recompute the risk of parents
        Unrated tickets have a risk of 0.5 and rating of 0.0!!
        """
        if 'my_rating' in values or 'parent_id' in values:
            old_values = [
                {'id': t.id,
                 'parent_id': t.parent_id.id,
                 'project_id': t.project_id.id}
                for t in self]
        res = super(Ticket, self).write(values)
        if 'my_rating' in values or 'parent_id' in values:
            # update the rating and risk (may be different for each ticket,
            # even if my_rating is the same)
            new_risk, new_rating = self.compute_risk_and_rating(self.ids)
            for ticket in self:
                super(Ticket, ticket).write({'risk': new_risk[ticket.id],
                                             'rating': new_rating[ticket.id]})
        # Propagate to the parents
        if 'my_rating' in values and 'parent_id' not in values:
            parents = self.browse(v['parent_id'] for v in old_values)
            parents.recompute_parents()
        elif values.get('parent_id'):
            # We reparented, we recompute the subnodes
            old_proj_ids = [v['project_id'] for v in old_values]
            new_proj_ids = self.browse(self.ids).project_id.ids
            all_projects = self.browse(list(set(old_proj_ids + new_proj_ids)))
            all_projects.recompute_subtickets()
        return res

    def create(self, values):
        """climb the tree up to the root and recompute
        """
        # ignore False or None ratings at creation in case the UI gives it
        if 'my_rating' in values and not values['my_rating']:
            values.pop('my_rating')
        ticket = super(Ticket, self).create(values)
        if values.get('my_rating'):
            new_risk, new_rating = self.compute_risk_and_rating([ticket.id])
            super(Ticket, ticket).write({'risk': new_risk[ticket.id],
                                         'rating': new_rating[ticket.id]})
        if values.get('parent_id'):
            self.browse(values.get('parent_id')).recompute_parents()
        return ticket

    def recompute_parents(self):
        """climb the tree starting from ids up to the root
        and recompute the risk and rating of each ticket.

        The overall rating is the sum of all the rating below.
        If we have 3 tickets with risks a, b, c,
        we compute the overall risk as: R3 = 1 - ((1-a)(1-b)-(1-c))^1/3
        """
        # ticket is the ticket that has been changed or reparented
        if not self:
            return
        for ticket in self:
            parent = ticket if ticket else None
            if not parent:
                continue
            # loop up to the root
            while parent:
                leafs = self.search([('id', 'child_of', parent.id),
                                     ('type.has_children', '=', False),
                                     ('id', '!=', parent.id)])
                if leafs:
                    rating = sum(leaf.rating for leaf in leafs)
                    risk = risk_mean(leaf.risk for leaf in leafs)
                    parent.write({'risk': risk, 'rating': rating})
                parent = parent.parent_id

    rating_ids = fields.One2many(
        'anytracker.rating',
        'ticket_id',
        'Ratings')
    highest_rating = fields.Many2one(
        'anytracker.complexity',
        compute=_highest_rating,
        string="Highest Rating")
    my_rating = fields.Many2one(
        'anytracker.complexity',
        compute=_get_my_rating,
        inverse=_set_my_rating,
        string="My Rating")
    risk = fields.Float(
        'Risk',
        group_operator="avg",
        default=0.5)
    color = fields.Char(
        compute=_color,
        string='Color')
    rating = fields.Float(
        'Rating',
        track_visibility='onchange',
        group_operator="sum")


class Method(models.Model):
    _inherit = 'anytracker.method'

    complexity_ids = fields.One2many(
        'anytracker.complexity',
        'method_id',
        'Complexities',
        copy=True,
        help="The complexities associated to this method")

    def copy(self, default=None):
        """ Customize the method copy
        """
        default = default or {}
        STAGE = self.env['anytracker.stage']
        COMPLEXITY = self.env['anytracker.complexity']
        new_method = super(Method, self).copy(default=default)
        # update forbidden complexities for new stages
        for old_stage in self.stage_ids:
            new_stages = STAGE.search([('state', '=', old_stage.state),
                                       ('method_id', '=', new_method.id)])
            if new_stages:
                new_stage = new_stages[0]
                # link to the equivalent forbidden complexities
                old_complexities = [
                    c.value for c in old_stage.forbidden_complexity_ids]
                if not old_complexities:
                    continue
                equiv_cmplx = COMPLEXITY.search(
                    [('value', 'in', old_complexities),
                     ('method_id', '=', new_stage.method_id.id)])
                new_stage.write({
                    'forbidden_complexity_ids': [(6, 0, equiv_cmplx.ids)]})
        return new_method
