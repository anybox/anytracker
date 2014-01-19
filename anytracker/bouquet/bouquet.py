import logging
from openerp.osv import osv, fields

logger = logging.getLogger(__file__)


BOUQUET_TYPES = (('changelog', u"Change log",),
                 )

class Bouquet(osv.Model):

    _name = 'anytracker.bouquet'
    _description = u"Ticket Bouquet"

    def _nb_tickets(self, cr, uid, ids, field_name, args, context=None):
        if isinstance(ids, (int, long)):
            ids = (ids,)
        cr.execute("SELECT bouquet_id, count(ticket_id) FROM anytracker_ticket_bouquet_rel "
                   "WHERE bouquet_id IN %s GROUP BY bouquet_id", (tuple(ids),))
        return dict(cr.fetchall())

    _columns = dict(
        name=fields.char(u'Name', size=128, required=True),
        description=fields.char(u'Description'),
        ticket_ids=fields.many2many('anytracker.ticket', 'anytracker_ticket_bouquet_rel',
                                    'bouquet_id', 'ticket_id', u"Tickets"),
        type=fields.selection(BOUQUET_TYPES, u"Type"),
        nb_tickets=fields.function(_nb_tickets, method=True, string=u'Number of tickets',
                                   type='integer',
                                   store=False, help='Full number of tickets in this bouquet'),
        create_date=fields.datetime('Creation Time'),
        write_date=fields.datetime('Modification Time'),
    )
