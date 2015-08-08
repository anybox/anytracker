# coding: utf-8
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class Stage(models.Model):
    """Add notifying config to the stage
    """
    _inherit = 'anytracker.stage'

    notify = fields.Boolean(
        u'Notify project members',
        help=u"Notify project members when a ticket enter this stage")
    notify_template_id = fields.Many2one(
        'email.template',
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
              u"Anytracker to send the notification each time the ticket reaches this stage"))


class Ticket(models.Model):
    """ Add notification feature
    """

    _inherit = 'anytracker.ticket'

    def check_notify(self, cr, uid, ticket):
        """ Return True only if we should notify
        """
        # no stage or no notify
        if not ticket.stage_id or not ticket.stage_id.notify:
            return False
        # mail already sent and don't send multiple times
        already_sent = [s.id for s in ticket.notified_stage_ids]
        if ticket.stage_id.id in already_sent and not ticket.stage_id.notify_multiple:
            return False
        # no mail template
        if not ticket.stage_id.notify_template_id:
            raise except_orm(
                _(u'Warning !'),
                _(u'No email template selected in the "%s" stage of the "%s" method'
                  % (ticket.stage_id.name, ticket.method_id.name)))
        return True

    def create(self, cr, uid, values, context=None):
        """ Notify on create
        """
        res = super(Ticket, self).create(cr, uid, values, context=context)
        ticket = self.browse(cr, uid, res, context)
        # don't sent a message already sent if configured as such
        if not self.check_notify(cr, uid, ticket):
            return res
        # remember that we sent a message for this stage, then send the message
        ticket.write({'notified_stage_ids': [(4, ticket.stage_id.id)]})
        self.pool.get('email.template').send_mail(
            cr, uid,
            ticket.stage_id.notify_template_id.id,
            ticket.id,
            force_send=ticket.stage_id.notify_urgent,
            context=context)
        return res

    def write(self, cr, uid, ids, values, context=None):
        """ Notify on write
        """
        res = super(Ticket, self).write(cr, uid, ids, values, context=context)
        if 'stage_id' not in values:
            return res
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for ticket in self.browse(cr, uid, ids, context):
            if not self.check_notify(cr, uid, ticket):
                return res
            ticket.write({'notified_stage_ids': [(4, ticket.stage_id.id)]})
            self.pool.get('email.template').send_mail(
                cr, uid,
                ticket.stage_id.notify_template_id.id,
                ticket.id,
                force_send=ticket.stage_id.notify_urgent,
                context=context)
        return res

    notified_stage_ids = fields.Many2many(
        'anytracker.stage',
        'anytracker_ticket_notif_rel',
        'ticket_id',
        'stage_id',
        'Notified stages')
