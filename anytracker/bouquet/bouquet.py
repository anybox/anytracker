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

    def _participant_ids(self, cr, uid, ids, field_name, args, context=None):
        if isinstance(ids, (int, long)):
            ids = (ids,)
        res = {}
        ticket = self.pool.get('anytracker.ticket')
        for bouquet_read in self.read(cr, uid, ids, ('ticket_ids',), context=context):
            all_parents_ids = set(
                t['id'] for tlist in ticket._breadcrumb(
                    cr, uid, bouquet_read['ticket_ids'], context=context).values()
                for t in tlist)
            res[bouquet_read['id']] = list(set(
                pid for t_read in ticket.read(cr, uid, list(all_parents_ids),
                                             ('participant_ids',), context=context)
                for pid in t_read['participant_ids']))

        return res

    def _search_participants(self, cr, uid, obj, field_name, domain, context=None):
        """Used as a fnct_search, and essential for ir_rule.

        This first implementation is expected to become very slow once there are lots of
        bouquets in the system. On the other hand, only storing the participants, e.g. making
        the function field a stored one would really do better.
        """
        assert(len(domain) == 1 and len(domain[0]) == 3)  # handle just this case
        (f, op, pids) = domain[0]
        assert(f == field_name)
        if op == 'in':
            if isinstance(pids, (int, long)):
                pids = (pids,)
            # shameful implementation : just list all available bouquets, their participants
            # and return a domain with the explicit list of matching bouquets
            all_bouquet_ids = self.search(cr, uid, [], context=context)
            participants_by_bouquet = self._participant_ids(cr, uid, all_bouquet_ids,
                                                            'participant_ids', (), context=context)
            return [('id', 'in',
                     [bid for bid, participant_ids in participants_by_bouquet.iteritems()
                      if not set(pids).isdisjoint(participant_ids)])]

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
        participant_ids=fields.function(_participant_ids, method=True,
                                        string=u'All participating users', type='many2many',
                                        fnct_search=_search_participants,
                                        relation='res.users'),
        project_ids=fields.function(_project_ids, method=True,
                                    string=u"Projects", type='many2many',
                                    relation='anytracker.ticket')
    )
