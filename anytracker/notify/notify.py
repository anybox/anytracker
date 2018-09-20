# coding: utf-8
from odoo import models, fields, _, api
from odoo.exceptions import except_orm


class Stage(models.Model):
    """Add notifying config to the stage
    """
    _inherit = 'anytracker.stage'

    notify = fields.Boolean(
        u'Notify project members',
        help=u"Notify project members when a ticket enter this stage")
    notify_template_id = fields.Many2one(
        'mail.template',
        u'Email template')
    notify_urgent = fields.Boolean(
        u'Urgent notification',
        help=u"Immediate notification (don't wait for email scheduler")
    notify_sms = fields.Boolean(
        u'SMS notification',
        help=u"NOT YET IMPLEMENTED (Enable SMS notification)")
    notify_multiple = fields.Boolean(
        u'Notify multiple times',
        help=(u"By default notifications are sent only once. "
              u"By checking this box you can force "
              u"Anytracker to send the notification"
              u" each time the ticket reaches this stage"))


class Ticket(models.Model):
    """ Add notification feature
    """
    _inherit = 'anytracker.ticket'

    def check_notify(self):
        """ Return True only if we should notify
        """
        # no stage or no notify
        if not self.stage_id or not self.stage_id.notify:
            return False
        # mail already sent and don't send multiple times
        if self.stage_id in self.notified_stage_ids:
            if not self.stage_id.notify_multiple:
                return False
        # no mail template
        if not self.stage_id.notify_template_id:
            raise except_orm(
                _(u'Warning !'),
                _(u"No email template selected "
                  u"in the '%s' stage of the '%s' method"
                  ) % (self.stage_id.name, self.method_id.name))
        return True

    @api.model
    def create(self, values):
        """ Notify on create
        """
        ticket = super(Ticket, self).create(values)
        # don't sent a message already sent if configured as such
        if not ticket.check_notify():
            return ticket
        # remember that we sent a message for this stage, then send the message
        ticket.write({'notified_stage_ids': [(4, ticket.stage_id.id)]})
        ticket.stage_id.notify_template_id.send_mail(
            ticket.id,
            force_send=ticket.stage_id.notify_urgent)
        return ticket

    @api.multi
    def write(self, values):
        """ Notify on write
        """
        res = super(Ticket, self).write(values)
        if 'stage_id' not in values:
            return res
        for ticket in self:
            if not ticket.check_notify():
                return res
            ticket.write({'notified_stage_ids': [(4, ticket.stage_id.id)]})
            ticket.stage_id.notify_template_id.send_mail(
                ticket.id,
                force_send=ticket.stage_id.notify_urgent)
        return res

    notified_stage_ids = fields.Many2many(
        'anytracker.stage',
        'anytracker_ticket_notif_rel',
        'ticket_id',
        'stage_id',
        'Notified stages')
