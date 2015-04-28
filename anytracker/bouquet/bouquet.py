import logging
from openerp.osv import fields
from openerp.osv import orm

logger = logging.getLogger(__file__)


BOUQUET_TYPES = (('changelog', u"Change log",),
                 )


class Bouquet(orm.Model):

    _name = 'anytracker.bouquet'
    _description = u"Ticket Bouquet"
    _order = 'create_date DESC'

    def _get_rating(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for bouquet in self.browse(cr, uid, ids):
            total = 0
            for ticket in bouquet.ticket_ids:
                if ticket.rating:
                    total = total+ticket.rating
            res[bouquet.id] = total
        return res

    def _nb_tickets(self, cr, uid, ids, field_name, args, context=None):
        if isinstance(ids, (int, long)):
            ids = (ids,)
        cr.execute("SELECT bouquet_id, count(ticket_id) FROM anytracker_ticket_bouquet_rel "
                   "WHERE bouquet_id IN %s GROUP BY bouquet_id", (tuple(ids),))
        return dict(cr.fetchall())

    def _project_ids(self, cr, uid, ids, field_name, args, context=None):
        if isinstance(ids, (int, long)):
            ids = (ids,)
        bouquet_reads = self.read(cr, uid, ids, ['ticket_ids'], context=context)
        all_tickets = set(tid for br in bouquet_reads for tid in br['ticket_ids'])
        # GR py 2.6 valid dict comprehension
        ticket = self.pool.get('anytracker.ticket')
        ticket_projects = dict(
            (tr['id'], tr['project_id'])
            for tr in ticket.read(cr, uid, list(all_tickets), ['project_id'],
                                  load='_classic_write', context=context))

        return dict((br['id'], list(set(ticket_projects[tid] for tid in br['ticket_ids'])))
                    for br in bouquet_reads)

    _columns = dict(
        name=fields.char(u'Name', size=128, required=True),
        description=fields.char(u'Description'),
        ticket_ids=fields.many2many('anytracker.ticket', 'anytracker_ticket_bouquet_rel',
                                    'bouquet_id', 'ticket_id', u"Tickets"),
        type=fields.selection(BOUQUET_TYPES, u"Type"),
        nb_tickets=fields.function(_nb_tickets, method=True, string=u'Number of tickets',
                                   type='integer',
                                   store=False, help='Full number of tickets in this bouquet'),
        create_date=fields.datetime('Creation Time', readonly=True),
        write_date=fields.datetime('Modification Time', readonly=True),
        participant_ids=fields.related('ticket_ids', 'project_id', 'participant_ids',
                                       string=u'All participating users', type='many2many',
                                       relation='res.users'),
        project_ids=fields.function(_project_ids, method=True,
                                    string=u"Projects", type='many2many',
                                    relation='anytracker.ticket'),
        bouquet_rating=fields.function(_get_rating, method=True,
                                       store=False,
                                       string=u"Rating", type='float'),
    )

    _defaults = {'bouquet_rating': 0}
