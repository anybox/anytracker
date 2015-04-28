# coding: utf-8
from openerp.osv import orm
from openerp.osv import fields
from tools.translate import _
import logging
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID

logger = logging.getLogger(__file__)


class Ticket(orm.Model):
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
                raise orm.except_orm(
                    _('Error'),
                    _("To be able to invoice a ticket, "
                      "you should set a product "
                      "on the corresponding project"))
            if not ticket.project_id.analytic_account_id:
                raise orm.except_orm(
                    _('Error'),
                    _("To be able to invoice a ticket, "
                      "you should set an analytic account "
                      "on the corresponding project"))
            if not ticket.rating:
                logger.warn(("Ticket #%s could not be invoiced "
                             "because it has no rating"), ticket.number)
                continue
            if ticket.type.has_children:
                raise orm.except_orm(
                    _('Error'),
                    _("Ticket #%s is a project or node. "
                      "It cannot be invoiced") % ticket.number)
            # on OCB the general account is not mandatory, but let's be compatible with openerp
            gen_account = ticket.project_id.product_id.property_account_expense
            if not gen_account and ticket.project_id.product_id.categ_id:
                gen_account = ticket.project_id.product_id.categ_id.property_account_expense_categ
            if not gen_account:
                raise orm.except_orm(
                    'Error', ("No expense account defined on the product (or category)"
                              " configured in your anytracker project"))
            if ticket.assigned_user_id:
                user_id = ticket.assigned_user_id.id
            elif ticket.rating_ids:
                user_id = ticket.rating_ids[0].user_id.id
            else:
                user_id = uid
            line_data = {
                'name': 'Ticket #%s: %s' % (ticket.number, ticket.name),
                'amount': 1.0,
                'unit_amount': ticket.rating,
                'to_invoice': ticket.project_id.analytic_account_id.to_invoice.id,
                'account_id': ticket.project_id.analytic_account_id.id,
                'product_id': ticket.project_id.product_id.id,
                'journal_id': ticket.project_id.analytic_journal_id.id,
                'general_account_id': gen_account.id,
                'user_id': user_id,
            }
            if ticket.priority_id and ticket.priority_id.discount_id:
                line_data['to_invoice'] = ticket.priority_id.discount_id.id
            line_data.update(analines.on_change_unit_amount(
                cr, uid, None, line_data['product_id'], line_data['unit_amount'], None,
                journal_id=line_data['journal_id'])['value'])
            line_id = analines.create(cr, uid, line_data)
            ticket.write({'analytic_line_id': line_id})
            result.append(line_id)
        return result

    def cron(self, cr, uid, context=None):
        super(Ticket, self).cron(cr, uid, context)
        # tickets to invoice
        yesterday = (datetime.now()-timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
        ticket_ids = self.search(cr, uid, [
            ('analytic_line_id', '=', False),
            ('progress', '=', 100.0),
            ('rating', '!=', 0.0),
            ('active', '=', True),
            ('write_date', '<=', yesterday),
            ('project_id.analytic_journal_id', '!=', False),
            ('project_id.product_id', '!=', False),
            ('project_id.analytic_account_id', '!=', False),
            ('type.has_children', '=', False),
        ])
        self.create_analytic_line(cr, uid, ticket_ids, context)

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


class Bouquet(orm.Model):
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


class Priority(orm.Model):
    """Add invoicing ratio to priorities
    """
    _inherit = 'anytracker.priority'
    _columns = {
        'discount_id': fields.many2one(
            'hr_timesheet_invoice.factor', 'Ratio',
            help=u'set the invoicing ratio for tickets with this priority')
    }


class account_analytic_line(orm.Model):
    """ Allow a customer to search analytic line by date (related to commit d6106d1aa13d)
    """
    _inherit = "account.analytic.line"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if len(args) == 1 and len(args[0]) == 3 and args[0][0] == 'date':
            uid = SUPERUSER_ID
        return super(account_analytic_line, self).search(cr, uid, args, offset, limit,
                                                         order, context=context, count=count)
