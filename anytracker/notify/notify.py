# coding: utf-8
from osv import fields, osv
from tools.translate import _


class Stage(osv.Model):
    """Add notifying config to the stage
    """
    _inherit = 'anytracker.stage'
    _columns = {
        'notify': fields.boolean(
            u'Notify project members',
            help=u"Notify project members when a ticket enter this stage"),
        'notify_template_id': fields.many2one(
            'email.template',
            u'Email template'),
        'notify_urgent': fields.boolean(
            u'Urgent notification',
            help=u"Immediate notification (don't wait for email scheduler"),
        'notify_sms': fields.boolean(
            u'SMS notification',
            help=u"NOT YET IMPLEMENTED (Enable SMS notification)"),
    }


class Ticket(osv.Model):
    """ Add notification feature
    """

    _inherit = 'anytracker.ticket'

    def check_notify(self, cr, uid, ticket):
        """ Return True only if we should notify
        """
        if not ticket.stage_id or not ticket.stage_id.notify:
            return False
        if not ticket.stage_id.notify_template_id:
            raise osv.except_osv(
                _(u'Warning !'),
                _(u'No email template selected in the "%s" "%s" stage of the "%s" method'
                  % (ticket.stage_id.name, ticket.method_id.name)))
        return True

    def create(self, cr, uid, values, context=None):
        """ Notify on create
        """
        res = super(Ticket, self).create(cr, uid, values, context=context)
        ticket = self.browse(cr, uid, res, context)
        if not self.check_notify(cr, uid, ticket):
            return res
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
        for ticket in self.browse(cr, uid, ids, context):
            if not self.check_notify(cr, uid, ticket):
                return res
            self.pool.get('email.template').send_mail(
                cr, uid,
                ticket.stage_id.notify_template_id.id,
                ticket.id,
                force_send=ticket.stage_id.notify_urgent,
                context=context)
        return res
