from osv import fields, osv
from tools.translate import _

class ticket(osv.osv):
    """Add risk functionnality to tickets
    """
    _inherit = 'anytracker.ticket'

    def _get_weighted_risk(self, cr, uid, ids, field_name, args, context=None):
        """get the overall risk of the ticket and number of tickets, based on subtickets.
        It should return a tuple with: a float, and the total number of ratings.
        Risk is defined by the mean of values defined in all ratings.
        """
        if not context: context = {}
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            # collect ratings from children
            ratings = [(i[0] or 0.0) for i in sum(
                self._get_weighted_risk(cr, uid,
                    [i.id for i in ticket.child_ids], field_name, context).values(),
                [])]
            nb_ratings = len(ratings)
            # no children, we are a leaf
            if nb_ratings == 0:
                ratings = [rating.complexity_id.value for rating in ticket.rating_ids]
                ratings = [v for v in ratings if v is not None]
                nb_ratings = len(ratings)
            # no ratings at all
            if nb_ratings == 0:
                risk, nb_ratings = (9999999, 1)
            else:
                risk, nb_ratings = (sum(ratings) / nb_ratings, nb_ratings)
            res[ticket.id] = [(risk, nb_ratings)]
        return res

    def _get_risk(self, cr, uid, ids, field_name, args, context=None):
        """ keep only the risk, skip the number
        """
        res = self._get_weighted_risk(cr, uid, ids, field_name, args, context)
        for i in res:
            res[i] = res[i][0][0]
        return res

    _columns = { 
        'risk': fields.function(_get_risk,
                                    method=True,
                                    type='float',
                                    string="Risk"),
     }
