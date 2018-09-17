from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import orm
from os.path import join
import anybox.testing.datetime  # noqa
from datetime import datetime, timedelta
import time


class TestInvoicing(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestInvoicing, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.BOUQUET = cls.env['anytracker.bouquet']
        cls.ANALINE = cls.env['account.analytic.line']
        cls.ANACCOUNT = cls.env['account.analytic.account']
        # #11390: analytic journal depreciated on v11
        #cls.ANAJOURNAL = cls.env['account.analytic.journal']

        USER = cls.env['res.users']
        cls.member_id = USER.create(
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]}
        ).id
        cls.customer_id = USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_customer')])]}
        ).id

    def test_invoicing(self):
        """ Check created analytic lines from a ticket
        """
        # we create a project with a team of 3 people
        project = self.TICKET.create(
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
             # #11390: analytic journal depreciated on v11
             #'analytic_journal_id': self.ANAJOURNAL.search([])[0].id,
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': self.ref('anytracker.method_test')})
        # we create a few tickets
        ticket1 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket1',
             'parent_id': project.id})
        ticket2 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket2',
             'parent_id': project.id})
        ticket3 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket3',
             'parent_id': project.id})
        ticket4 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket4',
             'parent_id': project.id, })

        # we cannot invoice until we haven't set an account on the project
        self.assertRaises(orm.except_orm, ticket1.create_analytic_line)

        # we create and set an account on the project
        account = self.ANACCOUNT.create({
            'name': 'project',
            'type': 'contract'})
        project.write({'analytic_account_id': account.id})

        # We try to invoice the unrated ticket 1
        ticket1.create_analytic_line()

        # we check there is no analytic lines created
        self.assertEquals(
            self.ANALINE.search([
                ('name', 'like', 'Invoiced ticket')], count=True),
            0)

        # We rate the ticket
        ticket1.write({'my_rating': self.ref('anytracker.complexity1')})

        # Once rated, the ticket can be invoiced successfully
        ticket1.create_analytic_line()

        # we check the content of the created analytic line
        analines = self.ANALINE.search([
            ('name', 'like', 'Invoiced ticket')])
        self.assertEquals(len(analines), 1)
        self.assertEquals(analines[0].name[-16:], 'Invoiced ticket1')

        # We rate tickets 2 and 3, but not the ticket 4
        ticket2.write({'my_rating': self.ref('anytracker.complexity2')})
        ticket3.write({'my_rating': self.ref('anytracker.complexity3')})

        # Now we create a bouquet with the 4 tickets
        bouquet = self.BOUQUET.create(
            {'name': 'bouquet',
             'ticket_ids': [(6, 0, [
                 ticket1.id, ticket2.id, ticket3.id, ticket4.id])]
             })
        # we launch invoicing on the bouquet itself
        bouquet.create_analytic_lines()

        # We should have only two more analytic lines:
        # Ticket1 in not invoiced twice and ticket4 is not invoiced
        self.assertEquals(
            self.ANALINE.search([
                ('name', 'like', 'Invoiced ticket')], count=True), 3)

        # We try to invoice the project itself. It should not do anything
        self.assertRaises(orm.except_orm, project.create_analytic_line)

    def test_invoicing_ratio(self):
        """ Test the different invoicing ratio
        """
        project = self.TICKET.create(
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
             # #11390: analytic journal depreciated on v11
             #'analytic_journal_id': self.ANAJOURNAL.search([])[0].id,
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': self.ref('anytracker.method_test')})
        account = self.ANACCOUNT.create({
            'name': 'project',
            'type': 'contract',
            'to_invoice': self.ref(
                'hr_timesheet_invoice.timesheet_invoice_factor1')})
        project.write({'analytic_account_id': account.id})
        # we create 3 tickets
        ticket1 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket1',
             'parent_id': project.id, })
        ticket2 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket2',
             'parent_id': project.id, })
        ticket3 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket3',
             'parent_id': project.id, })
        ticket4 = self.TICKET.with_context({'active_id': project.id}).create(
            {'name': 'Invoiced ticket4',
             'parent_id': project.id, })

        # we set ratings
        (ticket1 + ticket2 + ticket3 + ticket4).write({
            'my_rating': self.ref('anytracker.complexity1')})
        # we set priorities to the tickets 1 to 3 but not 4
        ticket1.write({
            'priority_id': self.ref('anytracker.test_prio_normal')})
        ticket2.write({
            'priority_id': self.ref('anytracker.test_prio_prio')})
        ticket3.write({
            'priority_id': self.ref('anytracker.test_prio_urgent')})

        # Now we create a bouquet with the 3 tickets
        bouquet = self.BOUQUET.create(
            {'name': 'bouquet',
             'ticket_ids': [(6, 0, [
                 ticket1.id, ticket2.id, ticket3.id, ticket4.id])]
             })
        # we launch invoicing on the bouquet
        bouquet.create_analytic_lines()

        # we check the ratio
        self.assertEquals(0, ticket1.analytic_line_id.to_invoice.factor)
        self.assertEquals(-40, ticket2.analytic_line_id.to_invoice.factor)
        self.assertEquals(-80, ticket3.analytic_line_id.to_invoice.factor)
        self.assertEquals(0, ticket4.analytic_line_id.to_invoice.factor)

    def test_cron(self):
        """ check that finished tickets are moved to invoicing after +24h
        """
        # run once before to invoice everything
        datetime.set_now(datetime.now() + timedelta(10))
        self.TICKET.cron()
        project = self.TICKET.create(
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
             'method_id': self.ref('anytracker.method_test')})
        # we create some tickets
        ticket1 = self.TICKET.create(
            {'name': 'Invoiced ticket1',
             'parent_id': project.id, })
        ticket2 = self.TICKET.create(
            {'name': 'Invoiced ticket2',
             'parent_id': project.id, })
        ticket3 = self.TICKET.create(
            {'name': 'Invoiced ticket3',
             'parent_id': project.id, })
        ticket4 = self.TICKET.create(
            {'name': 'Invoiced ticket4',
             'parent_id': project.id, })
        (ticket1 + ticket3).write({
            'my_rating': self.ref('anytracker.complexity1')})
        # also fake the create_date and write_date
        # because anybox.testing.datetime can't work
        # for postgresql now() function
        self.env.cr.execute(
            'update anytracker_ticket set create_date=%s, write_date=%s '
            'where id in (%s, %s, %s, %s)',
            (time.strftime('%Y-%m-%d %H:%M:%S'),
             time.strftime('%Y-%m-%d %H:%M:%S'),
             ticket1.id, ticket2.id, ticket3.id, ticket4.id))

        def count_invoiced():
            return len(self.TICKET.search([('analytic_line_id', '!=', False)]))

        previous_count = count_invoiced()

        # now set the 2 tickets as finished
        (ticket1 + ticket3).write({
            'stage_id': self.ref('anytracker.stage_test_done')})
        self.env.cr.execute(
            'update anytracker_ticket set write_date=%s '
            'where id in (%s, %s)',
            (time.strftime('%Y-%m-%d %H:%M:%S'), ticket1.id, ticket3.id))
        # relaunch the cron, still nothing invoiced
        self.TICKET.cron()
        self.assertEquals(previous_count, count_invoiced())

        # now fill the missing data in the project,
        # we still have 0 tickets invoiced
        account = self.ANACCOUNT.create({
            'name': 'project',
            'type': 'contract'})
        project.write({
            # #11390: analytic journal depreciated on v11
            #'analytic_journal_id': self.ANAJOURNAL.search([])[0].id,
            'product_id': self.ref('product.product_product_consultant'),
            'analytic_account_id': account.id})
        self.TICKET.cron()
        self.assertEquals(previous_count, count_invoiced())

        # we should wait +24h, so we set the time to tomorrow and run the cron
        datetime.set_now(datetime.now() + timedelta(1))
        self.TICKET.cron()
        self.assertEquals(previous_count + 2, count_invoiced())
        datetime.real_now()
