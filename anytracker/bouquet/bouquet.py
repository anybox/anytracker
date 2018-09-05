#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api

logger = logging.getLogger(__file__)

BOUQUET_TYPES = (('changelog', u"Change log",),
                 )


class Bouquet(models.Model):
    _name = 'anytracker.bouquet'
    _description = u"Ticket Bouquet"
    _order = 'create_date DESC'

    @api.depends('ticket_ids')
    def _get_rating(self):
        for bouquet in self:
            total = 0
            for ticket in bouquet.ticket_ids:
                if ticket.rating:
                    total = total + ticket.rating
            bouquet.bouquet_rating = total

    def _nb_tickets(self):
        cr = self.env.cr
        cr.execute(
            "SELECT bouquet_id, count(ticket_id)"
            " FROM anytracker_ticket_bouquet_rel"
            " WHERE bouquet_id IN %s GROUP BY bouquet_id",
            (tuple(self.ids),))
        res = dict(cr.fetchall())
        for bouquet in self:
            bouquet.nb_tickets = res[bouquet.id]

    @api.depends('ticket_ids')
    def _project_ids(self):
        for bouquet in self:
            projects = list({t.project_id.id for t in bouquet.ticket_ids})
            bouquet.project_ids = projects

    name = fields.Char(
        u'Name',
        size=128,
        required=True)
    description = fields.Char(
        u'Description')
    ticket_ids = fields.Many2many(
        'anytracker.ticket',
        'anytracker_ticket_bouquet_rel',
        'bouquet_id',
        'ticket_id',
        u"Tickets")
    type = fields.Selection(
        BOUQUET_TYPES,
        u"Type")
    nb_tickets = fields.Integer(
        compute=_nb_tickets,
        string=u'Number of tickets',
        help='Full number of tickets in this bouquet')
    create_date = fields.Datetime(
        string='Creation Time',
        readonly=True)
    write_date = fields.Datetime(
        string='Modification Time',
        readonly=True)
    participant_ids = fields.Many2many(
        related='ticket_ids.project_id.participant_ids',
        string=u'All participating users', )
    project_ids = fields.Many2many(
        'anytracker.ticket',
        compute=_project_ids,
        string=u"Projects")
    bouquet_rating = fields.Float(
        compute=_get_rating,
        default=0.0,
        method=True,
        string=u"Rating", )
