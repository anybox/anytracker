import logging
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

logger = logging.getLogger(__file__)

BOUQUET_TYPES = (('changelog', u"Change log",),
                 )


class Bouquet(models.Model):
    _name = 'anytracker.bouquet'
    _description = u"Ticket Bouquet"
    _order = 'create_date DESC'

    @api.one
    def _get_rating(self):
        res = {}
        total = 0
        for ticket in self.ticket_ids:
            if ticket.rating:
                total = total + ticket.rating
        self.bouquet_rating = total

    @api.one
    def _nb_tickets(self):
        self._cr.execute("SELECT bouquet_id, count(ticket_id) FROM anytracker_ticket_bouquet_rel "
                   "WHERE bouquet_id IN %s GROUP BY bouquet_id", (tuple([self.ids]),))
        self.nb_tickets =  dict(self._cr.fetchall())

    @api.one
    def _project_ids(self):
        # if isinstance(ids, (int, long)):
        #     ids = (ids,)
        all_tickets = self.browse().ticket_ids
        # all_tickets = set(tid for br in bouquet_reads for tid in br['ticket_ids'])
        # GR py 2.6 valid dict comprehension
        ticket = self.env['anytracker.ticket']
        ticket_projects = dict(
            (tr['id'], tr['project_id'])
            for tr in all_tickets.project_id)

        self.project_ids = ticket_projects

    name = fields.Char(u'Name', size=128, required=True)
    description = fields.Char(u'Description')
    ticket_ids = fields.Many2many('anytracker.ticket', 'anytracker_ticket_bouquet_rel',
                                  'bouquet_id', 'ticket_id', u"Tickets")
    type = fields.Selection(BOUQUET_TYPES, u"Type")
    nb_tickets = fields.Integer(compute='_nb_tickets', string=u'Number of tickets',
                                store=False, help='Full number of tickets in this bouquet')
    create_date = fields.Datetime(string='Creation Time', readonly=True)
    write_date = fields.Datetime(string='Modification Time', readonly=True)
    participant_ids = fields.Many2many('res.users', 'ticket_ids', 'project_id', 'participant_ids',
                                       string=u'All participating users', )
    project_ids = fields.Many2many('anytracker.ticket', compute='_project_ids',
                                   string=u"Projects")
    bouquet_rating = fields.Float(compute='_get_rating', method=True,
                                  store=False,
                                  string=u"Rating", )

    _defaults = {'bouquet_rating': 0}
