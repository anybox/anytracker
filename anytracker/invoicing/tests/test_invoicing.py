from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import osv
from os.path import join
import anybox.testing.datetime  # noqa
from datetime import datetime, timedelta
import time


class TestInvoicing(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(self):
        super(TestInvoicing, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.bouquets = self.registry('anytracker.bouquet')
        self.users = self.registry('res.users')
        self.analines = self.registry('account.analytic.line')
        self.anaccounts = self.registry('account.analytic.account')
        self.anajournals = self.registry('account.analytic.journal')

        self.member_id = self.users.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_member'),
                            self.ref('base.group_user')])]})
        self.customer_id = self.users.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_customer')])]})

    def test_invoicing(self):
        """ Check created analytic lines from a ticket
        """
        cr, uid = self.cr, self.uid
        # we create a project with a team of 3 people
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
             'analytic_journal_id': self.anajournals.search(cr, uid, [])[0],
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': self.ref('anytracker.method_test')})
        # we create a few tickets
        ticket1_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket1',
             'parent_id': project_id, },
            context={'active_id': project_id})
        ticket2_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket2',
             'parent_id': project_id, },
            context={'active_id': project_id})
        ticket3_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket3',
             'parent_id': project_id, },
            context={'active_id': project_id})
        ticket4_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket4',
             'parent_id': project_id, },
            context={'active_id': project_id})

        # we cannot invoice until we haven't set an account on the project
        self.assertRaises(osv.except_osv,
                          self.tickets.create_analytic_line,
                          cr, uid, [ticket1_id])

        # we create and set an account on the project
        account_id = self.anaccounts.create(cr, uid, {
            'name': 'project',
            'type': 'contract'})
        self.tickets.write(cr, uid, [project_id], {
            'analytic_account_id': account_id})

        # We try to invoice the unrated ticket 1
        self.tickets.create_analytic_line(cr, uid, [ticket1_id])

        # we check there is no analytic line created
        self.assertEquals(
            self.analines.search(cr, uid, [('name', 'like', 'Invoiced ticket')], count=True), 0)

        # We rate the ticket
        self.tickets.write(cr, uid, [ticket1_id], {
            'my_rating': self.ref('anytracker.complexity1')})

        # Once rated, the ticket can be invoiced successfully
        self.tickets.create_analytic_line(cr, uid, [ticket1_id])

        # we check the content of the created analytic line
        analines = self.analines.search(cr, uid, [('name', 'like', 'Invoiced ticket')])
        self.assertEquals(len(analines), 1)
        self.assertEquals(
            self.analines.browse(cr, uid, analines[0]).name[-16:],
            'Invoiced ticket1')

        # We rate tickets 2 and 3, but not the ticket 4
        self.tickets.write(cr, uid, [ticket2_id], {
            'my_rating': self.ref('anytracker.complexity2')})
        self.tickets.write(cr, uid, [ticket3_id], {
            'my_rating': self.ref('anytracker.complexity3')})

        # Now we create a bouquet with the 4 tickets
        bouquet_id = self.bouquets.create(
            cr, uid,
            {'name': 'bouquet',
             'ticket_ids': [(6, 0, [ticket1_id, ticket2_id, ticket3_id, ticket4_id])]
             })
        # we launch invoicing on the bouquet itself
        self.bouquets.create_analytic_lines(cr, uid, [bouquet_id])

        # We should have only two more analytic lines:
        # Ticket1 in not invoiced twice and ticket4 is not invoiced
        self.assertEquals(
            self.analines.search(cr, uid, [('name', 'like', 'Invoiced ticket')], count=True), 3)

        # We try to invoice the project itself. It should not do anything
        self.assertRaises(osv.except_osv,
                          self.tickets.create_analytic_line,
                          cr, uid, [project_id])

    def test_invoicing_ratio(self):
        """ Test the different invoicing ratio
        """
        cr, uid = self.cr, self.uid
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
             'analytic_journal_id': self.anajournals.search(cr, uid, [])[0],
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': self.ref('anytracker.method_test')})
        account_id = self.anaccounts.create(cr, uid, {
            'name': 'project',
            'type': 'contract',
            'to_invoice': self.ref('hr_timesheet_invoice.timesheet_invoice_factor1')})
        self.tickets.write(cr, uid, [project_id], {
            'analytic_account_id': account_id})
        # we create 3 tickets
        ticket1_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket1',
             'parent_id': project_id, },
            context={'active_id': project_id})
        ticket2_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket2',
             'parent_id': project_id, },
            context={'active_id': project_id})
        ticket3_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket3',
             'parent_id': project_id, },
            context={'active_id': project_id})
        ticket4_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket4',
             'parent_id': project_id, },
            context={'active_id': project_id})

        # we set ratings
        self.tickets.write(cr, uid, [ticket1_id, ticket2_id, ticket3_id, ticket4_id], {
            'my_rating': self.ref('anytracker.complexity1')})
        # we set priorities to the tickets 1 to 3 but not 4
        self.tickets.write(cr, uid, [ticket1_id], {
            'priority_id': self.ref('anytracker.test_prio_normal')})
        self.tickets.write(cr, uid, [ticket2_id], {
            'priority_id': self.ref('anytracker.test_prio_prio')})
        self.tickets.write(cr, uid, [ticket3_id], {
            'priority_id': self.ref('anytracker.test_prio_urgent')})

        # Now we create a bouquet with the 3 tickets
        bouquet_id = self.bouquets.create(
            cr, uid,
            {'name': 'bouquet',
             'ticket_ids': [(6, 0, [ticket1_id, ticket2_id, ticket3_id, ticket4_id])]
             })
        # we launch invoicing on the bouquet
        self.bouquets.create_analytic_lines(cr, uid, [bouquet_id])

        # we check the ratio
        self.assertEquals(
            0,
            self.tickets.browse(cr, uid, ticket1_id).analytic_line_id.to_invoice.factor)
        self.assertEquals(
            -40,
            self.tickets.browse(cr, uid, ticket2_id).analytic_line_id.to_invoice.factor)
        self.assertEquals(
            -80,
            self.tickets.browse(cr, uid, ticket3_id).analytic_line_id.to_invoice.factor)
        self.assertEquals(
            0,
            self.tickets.browse(cr, uid, ticket4_id).analytic_line_id.to_invoice.factor)

    def test_cron(self):
        """ check that finished tickets are moved to invoicing after +24h
        """
        cr, uid = self.cr, self.uid
        # run once before to invoice everything
        datetime.set_now(datetime.now() + timedelta(10))
        self.tickets.cron(cr, uid)
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
             'method_id': self.ref('anytracker.method_test')})
        # we create some tickets
        ticket1_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket1',
             'parent_id': project_id, })
        ticket2_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket2',
             'parent_id': project_id, })
        ticket3_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket3',
             'parent_id': project_id, })
        ticket4_id = self.tickets.create(
            cr, uid,
            {'name': 'Invoiced ticket4',
             'parent_id': project_id, })
        self.tickets.write(cr, uid, [ticket1_id, ticket3_id], {
            'my_rating': self.ref('anytracker.complexity1')})
        # also fake the create_date and write_date
        # because anybox.testing.datetime doesn't work for postgresql now() function
        cr.execute('update anytracker_ticket set create_date=%s, write_date=%s '
                   'where id in (%s, %s, %s, %s)',
                   (time.strftime('%Y-%m-%d %H:%M:%S'), time.strftime('%Y-%m-%d %H:%M:%S'),
                    ticket1_id, ticket2_id, ticket3_id, ticket4_id))

        def count_invoiced():
            return len(self.tickets.search(cr, uid, [('analytic_line_id', '!=', False)]))

        previous_count = count_invoiced()

        # now set the 2 tickets as finished
        self.tickets.write(cr, uid, [ticket1_id, ticket3_id],
                           {'stage_id': self.ref('anytracker.stage_test_done')})
        cr.execute('update anytracker_ticket set write_date=%s '
                   'where id in (%s, %s)',
                   (time.strftime('%Y-%m-%d %H:%M:%S'), ticket1_id, ticket3_id))
        # relaunch the cron, still nothing invoiced
        self.tickets.cron(cr, uid)
        self.assertEquals(previous_count, count_invoiced())

        # now fill the missing data in the project, we still have 0 tickets invoiced
        account_id = self.anaccounts.create(cr, uid, {
            'name': 'project',
            'type': 'contract'})
        self.tickets.write(cr, uid, project_id,
                           {'analytic_journal_id': self.anajournals.search(cr, uid, [])[0],
                            'product_id': self.ref('product.product_product_consultant'),
                            'analytic_account_id': account_id})
        self.tickets.cron(cr, uid)
        self.assertEquals(previous_count, count_invoiced())

        # we should wait +24h, so we set the time to tomorrow and run the cron
        datetime.set_now(datetime.now() + timedelta(1))
        self.tickets.cron(cr, uid)
        self.assertEquals(previous_count + 2, count_invoiced())
        datetime.real_now()
