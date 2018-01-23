# coding: utf-8
from openerp import models, fields, api, _


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


class Link(models.Model):
    """Link.
    """
    _name = 'anytracker.link'

    def return_action_ticket(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'name': _('Ticket'),
            'res_model': 'anytracker.ticket',
            'view_type': 'tree',
            'view_mode': 'tree',
            'target': 'current',
            'nodestroy': True,
        }

    @api.multi
    def action_delete_link(self):
        for link in self:
            link.unlink()
        return self.return_action_ticket()

    @api.multi
    def action_open_link(self):
        assert len(self) == 1, ('This option should only be used '
                                'for a single id at a time.')
        # template = self.env.ref('account.email_template_edi_invoice', False)
        id = self.id
        return {
            'name': self.id,
            'res_model': 'anytracker.link',
            'res_id': id,
            'type': 'ir.actions.act_window',
            'context': {},
            'view_mode': 'form',
            'view_type': 'form',
            # 'view_id': self.env.ref('view_prod_order_form'),
            'target': 'new',  # 'target': 'current',
            'flags': {'form': {'action_buttons': True}}

        }

    @api.one
    @api.depends('ticket_two', 'ticket_one')
    @api.onchange('ticket_two', 'ticket_one')
    def _data_tickets(self):

        for link in self:
            if 'active_id' in self.env.context and self.env.context['active_id']:
                active_id = self.env.context['active_id']
                if link.ticket_one:
                    if link.ticket_one.id != active_id:
                        link.name = link.ticket_one.name
                        link.number = link.ticket_one.number
                        link.stage = link.ticket_one.stage_id.name
                        link.progress = link.ticket_one.progress

                if link.ticket_two:
                    if link.ticket_two.id != active_id:
                        link.name = link.ticket_two.name
                        link.number = link.ticket_two.number
                        link.stage = link.ticket_two.stage_id.name
                        link.progress = link.ticket_two.progress
            else:
                link.name = False
                link.number = False
                link.stage = False
                link.progress = False

    ticket_one = fields.Many2one(
        'anytracker.ticket',
        'Ticket one',
        required=True,
        ondelete='cascade')
    ticket_two = fields.Many2one(
        'anytracker.ticket',
        'Ticket two',
        required=True,
        ondelete='cascade')

    linktype_id = fields.Many2one(
        'anytracker.link.type',
        'Type Link',
        required=False,
        ondelete='cascade')
    name = fields.Char(compute='_data_tickets', string="")
    number = fields.Char(compute='_data_tickets', string="")
    progress = fields.Float(compute='_data_tickets', string="")
    stage = fields.Char(compute='_data_tickets', string="")


class Ticket(models.Model):
    """ Add links
    """
    _inherit = 'anytracker.ticket'

    @api.one
    def _getAllLink(self):
        LINK_MODEL = self.env['anytracker.link']
        for ticket in self:
            ticket.all_links = LINK_MODEL.search(
                ['|', ('ticket_two', '=', ticket.id),
                      ('ticket_one', '=', ticket.id)])

    @api.multi
    def action_add_link(self):
        assert len(self) == 1, ('This option should only be used '
                                'for a single id at a time.')
        # template = self.env.ref('account.email_template_edi_invoice', False)
        return {
            'name': "add new link",
            'res_model': 'anytracker.link',
            # 'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_ticket_one': self.id},
            # 'view_id': self.env.ref('view_prod_order_form'),
            'target': 'new',  # 'target': 'current',
            'flags': {'form': {'action_buttons': True}}

        }

    link_ids = fields.One2many(
        'anytracker.link',
        'ticket_one',
        'Links',
        copy=True,
        help="The tickets linked to this tickets")
    all_links = fields.One2many(
        'anytracker.link',
        string="links",
        compute='_getAllLink')
