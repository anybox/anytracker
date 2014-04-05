# coding: utf-8
from openerp.osv import fields, osv
from tools.translate import _
import logging

logger = logging.getLogger(__file__)


class Ticket(osv.Model):
    """ Allow to invoice a single ticket
    """

    _inherit = 'anytracker.ticket'

    def create_analytic_line(self, cr, uid, ids, context=None):
        """ Create an analytic line for each ticket
        """
        result = []
        analines = self.pool.get('account.analytic.line')
        for ticket in self.browse(cr, uid, ids, context):
            if ticket.analytic_line_id:
                continue
            if not ticket.project_id.product_id:
                raise osv.except_osv(
                    _('Error'),
                    _("To be able to invoice a ticket, "
                      "you should set a product "
                      "on the corresponding project"))
            if not ticket.project_id.analytic_account_id:
                raise osv.except_osv(
                    _('Error'),
                    _("To be able to invoice a ticket, "
                      "you should set an analytic account "
                      "on the corresponding project"))
            if not ticket.rating:
                logger.warn(("Ticket #%s could not be invoiced "
                             "because it has no rating"), ticket.number)
                continue
            if ticket.child_ids:
                raise osv.except_osv(
                    _('Error'),
                    _("Ticket #%s is a project or node. "
                      "It cannot be invoiced") % ticket.number)
            # on OCB the general account is not mandatory, but let's be compatible with openerp
            gen_account = ticket.project_id.product_id.property_account_expense
            if not gen_account and ticket.project_id.product_id.categ_id:
                gen_account = ticket.project_id.product_id.categ_id.property_account_expense_categ
            if not gen_account:
                raise osv.except_osv(
                    'Error', ("No expense account defined on the product (or category)"
                              " configured in your anytracker project"))
            line_id = analines.create(cr, uid, {
                'name': 'Ticket #%s: %s' % (ticket.number, ticket.name),
                'amount': 1.0,
                'unit_amount': ticket.rating,
                'to_invoice': ticket.project_id.analytic_account_id.to_invoice.id,
                'account_id': ticket.project_id.analytic_account_id.id,
                'product_id': ticket.project_id.product_id.id,
                'journal_id': ticket.project_id.analytic_journal_id.id,
                'general_account_id': gen_account.id,
            })
            ticket.write({'analytic_line_id': line_id})
            result.append(line_id)
        return result

    _columns = {
        'analytic_account_id': fields.many2one(
            'account.analytic.account',
            'Analytic account / project',
            help=(u"Choose the analytic account or project on which "
                  u"to create analytic lines to invoice")),
        'analytic_line_id': fields.many2one(
            'account.analytic.line',
            'Analytic line',
            help=(u"The analytic line used to invoice the ticket")),
        'product_id': fields.many2one(
            'product.product',
            'Product to invoice',
            help=(u"The product to invoice")),
        'analytic_journal_id': fields.many2one(
            'account.analytic.journal',
            'Analytic journal',
            help=(u"Analytic journal to use when invoicing")),
    }


class Bouquet(osv.Model):
    """ Allow to invoice all the tickets of the bouquet
    """
    _inherit = "anytracker.bouquet"

    def create_analytic_lines(self, cr, uid, ids, context=None):
        """ Create analytic lines of for all tickets of the bouquet
        """
        tickets = self.pool.get('anytracker.ticket')
        for bouquet in self.browse(cr, uid, ids, context):
            ticket_ids = [t.id for t in bouquet.ticket_ids]
            tickets.create_analytic_line(cr, uid, ticket_ids)
