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
            #'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
       }

    @api.multi
    def action_delete_link(self):
        LINK_MODEL = self.env['anytracker.link']
        for rec in self:
            self.unlink()
        return self.return_action_ticket()

    @api.multi
    def action_open_link(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
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
    @api.depends('ticket_two')
    @api.onchange('ticket_two')
    def _data_tickets(self):
        for rec in self:
            if rec.ticket_one:
                 if rec.ticket_one.id!=rec._context['active_ticket']:
                    self.name = rec.ticket_one.name
                    self.number = rec.ticket_one.number
                    self.stage = rec.ticket_one.stage_id.name
                    self.progress = rec.ticket_one.progress

            if rec.ticket_two:
                 if rec.ticket_two.id!=rec._context['active_ticket']:
                    self.name = rec.ticket_two.name
                    self.number = rec.ticket_two.number
                    self.stage = rec.ticket_two.stage_id.name
                    self.progress = rec.ticket_two.progress


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
        all_link = False
        LINK_MODEL = self.env['anytracker.link']
        for rec in self:
            rec.all_links = LINK_MODEL.search(['|',('ticket_two', '=', rec.id),('ticket_one', '=', rec.id)])

    @api.multi
    def action_add_link(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        # template = self.env.ref('account.email_template_edi_invoice', False)
        id = self.id
        return {
            'name': "add new link",
            'res_model': 'anytracker.link',
            # 'res_id': id,
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
    all_links = fields.One2many('anytracker.link',string="links",compute='_getAllLink')