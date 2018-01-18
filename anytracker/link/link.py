# coding: utf-8
from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class LinkType(models.Model):
    """Type of a link.
    """
    _name = 'anytracker.link.type'
    _order = 'name'

    name = fields.Char(
        'name',
        size=64,
        required=True,
        translate=True)
    description = fields.Text(
        'Description',
        translate=True)
    state = fields.Char(
        'state',
        size=64,
        required=True)
    linktype_id = fields.Many2one(
        'anytracker.link.type',
        'Reverse Link Type',
         required=False,
         ondelete='cascade')

class Link(models.Model):
    """Link.
    """
    _name = 'anytracker.link'

    @api.one
    @api.depends('ticket_two')
    @api.onchange('ticket_two')
    def _data_tickets(self):
        for rec in self:
            if rec.ticket_one:
                self.stage1 = rec.ticket_one.stage_id.name
                self.progress1 = rec.ticket_one.progress
                self.number1 = rec.ticket_one.number
            else:
                self.stage1 = False
                self.progress1 = False
                self.number1 = False
            if rec.ticket_two:
                self.stage2 = rec.ticket_two.stage_id.name
                self.progress2 = rec.ticket_two.progress
                self.number2 = rec.ticket_two.number
            else:
                self.stage2 = False
                self.progress2 = False
                self.number2 = False

    ticket_one =  fields.Many2one(
        'anytracker.ticket',
        'Ticket one',
         required=True,
         ondelete='cascade')
    ticket_two =  fields.Many2one(
        'anytracker.ticket',
        'Ticket two',
         required=True,
         ondelete='cascade')

    linktype_id = fields.Many2one(
        'anytracker.link.type',
        'Type Link',
         required=False,
         ondelete='cascade')
    number1 = fields.Char(compute='_data_tickets', string="")
    progress1 = fields.Float(compute='_data_tickets', string="")
    stage1 = fields.Char(compute='_data_tickets', string="")
    number2 = fields.Char(compute='_data_tickets', string="")
    progress2 = fields.Float(compute='_data_tickets', string="")
    stage2 = fields.Char(compute='_data_tickets', string="")


class Ticket(models.Model):
    """ Add links
    """
    _inherit = 'anytracker.ticket'

    @api.one
    def _getAllLink(self):
        all_link = False
        LINK_MODEL = self.env['anytracker.link']

        for rec in self:
            rec.all_links = LINK_MODEL.search(['|',('ticket_two', '=', rec.id),('ticket_one', '=', rec.id)])



    link_ids = fields.One2many(
        'anytracker.link',
        'ticket_one',
        'Links',
        copy=True,
        help="The tickets linked to this tickets")
    all_links = fields.One2many('anytracker.link',string="links",compute='_getAllLink')