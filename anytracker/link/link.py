# -*- coding: utf-8 -*-
from odoo.exceptions import Warning
from odoo import models, fields, api, _


class LinkType(models.Model):
    """Type of a link.
    """
    _name = 'anytracker.link.type'
    _description = "Link type"
    _order = 'name'

    name = fields.Char(
        _("name"),
        size=64,
        required=True,
        translate=True)
    description = fields.Text(
        _('Description'),
        translate=True)


class Link(models.Model):
    """The link is used to link 2 tickets.
    For example it is useful to link use case ticket with few technical ticket
    A ticket can be present in several links.
    """
    _name = 'anytracker.link'
    _description = "Link between two tickets"

    @api.depends('ticket_two', 'ticket_one')
    @api.onchange('ticket_two', 'ticket_one')
    def _data_tickets(self):
        # This function is used for ticket view
        # to display the list of active ticket links
        # In the link,  the active ticket can be ticket_one or ticket_two,
        # the goal is to display the ticket is not active ticket

        for link in self:
            if self.env.context.get('active_id'):
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
        ondelete='cascade',
    )

    linktype_id = fields.Many2one(
        'anytracker.link.type',
        'Type Link',
        required=True,
        ondelete='cascade')

    name = fields.Char(compute='_data_tickets', string="")
    number = fields.Char(compute='_data_tickets', string="")
    progress = fields.Float(compute='_data_tickets', string="")
    stage = fields.Char(compute='_data_tickets', string="")

    @api.multi
    def name_get(self):
        """ set a displaying to better represent link between two tickets """

        result = []

        for link in self:
            diaplay_value = "{} <-> {}".format(
                link.ticket_one.number, link.ticket_two.number)
            result.append((link.id, diaplay_value))

            return result

    def return_action_ticket(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'name': 'Ticket',
            'res_model': 'anytracker.ticket',
            'view_type': 'tree',
            'view_mode': 'tree',
            'target': 'current',
            'nodestroy': True,
        }

    @api.multi
    def action_delete_link(self):
        # FIXME - Is there no verification to be done before deleting a link?
        self.unlink()
        return self.return_action_ticket()

    @api.multi
    def action_open_link(self):
        self.ensure_one()

        return {
            'name': self.name,
            'res_model': 'anytracker.link',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {},
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            #'flags': {'form': {'action_buttons': True}}  #11387 replaced by custom buttons
        }

    @api.multi
    def action_open_linked_ticket(self):
        self.ensure_one()

        if self.env.context.get('active_id'):
            active_id = self.env.context['active_id']
            source_ticket = self.browse(active_id)
            co_ticket = source_ticket.ticket_one == active_id \
                and source_ticket.ticket_one or source_ticket.ticket_two

            return {
                'name': co_ticket.name,
                'res_model': 'anytracker.ticket',
                'res_id': co_ticket.id,
                'type': 'ir.actions.act_window',
                'context': {},
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
            }

        return {}

    @api.multi
    def dummy(self):
        """
        #11387 dummy save button refresh action (replaces legacy save button)
        will refresh links o2m of active ticket
        """
        return {}


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

        # This will make sure we have on record, not multiple records.
        self.ensure_one()

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

    def _compute_linkables(self):
        for rec in self:
            rec.linkables = True

    def _compute_search_linkables(self, operator, value):
        if operator != '=' and not isinstance(value, bool):
            Warning(_('search_to_link field: not valid operator/value'))

        if self.env.context.get('active_id'):
            # active ticket
            active_id = self.env.context.get('active_id')

            # exclude active ticket itself
            ids = [active_id]

            # linked tickets
            links_recset = self.env['anytracker.link'].search([
                '|',
                ('ticket_two', '=', active_id),
                ('ticket_one', '=', active_id)
            ])
            linked_tickets_ids = []
            for link in links_recset:
                linked_tickets_ids.append(link.ticket_one.id)
                linked_tickets_ids.append(link.ticket_two.id)
            if linked_tickets_ids:
                ids += linked_tickets_ids
            ids = list(set(linked_tickets_ids))  # remove duplicates active_id included

            return [('id', value and 'not in' or 'in', ids)]
        return []

    # get tickets that are not already linked to current active ticket
    linkables = fields.Boolean(
        compute='_compute_linkables',
        search='_compute_search_linkables'
    )
