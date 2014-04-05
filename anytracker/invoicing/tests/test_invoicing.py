from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import osv


class TestInvoicing(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestInvoicing, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.bouquets = self.registry('anytracker.bouquet')
        self.user = self.registry('res.users')
        self.ratings = self.registry('anytracker.rating')
        self.analines = self.registry('account.analytic.line')
        self.anaccounts = self.registry('account.analytic.account')
        self.anajournals = self.registry('account.analytic.journal')

        self.member_id = self.user.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_member'),
                            self.ref('base.group_user')])]})
        self.customer_id = self.user.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_customer')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        quickstart_method = self.ref('anytracker.method_quickstart')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Quickstart test',
             'participant_ids': [(6, 0, participant_ids)],
             'analytic_journal_id': self.anajournals.search(cr, uid, [])[0],
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': quickstart_method})
        return project_id

    def test_invoicing(self):
        """ Check created analytic lines from a ticket
        """
        cr, uid = self.cr, self.uid
        # we create a project with a team of 3 people
        project_id = self.createProject([self.customer_id, self.member_id])
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
            'my_rating': self.ref('anytracker.complexity_1h')})

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
            'my_rating': self.ref('anytracker.complexity_2h')})
        self.tickets.write(cr, uid, [ticket3_id], {
            'my_rating': self.ref('anytracker.complexity_4h')})

        # Now we create a bouquet with the 4 tickets
        bouquet_id = self.bouquets.create(
            cr, uid,
            {'name': 'bouquet',
             'ticket_ids': [(6, 0, [ticket1_id, ticket2_id, ticket3_id, ticket4_id])]
             })
        # we launch invoicing on the bouquet itself
        self.bouquets.create_analytic_lines(cr, uid, [bouquet_id])

        # We should have only only two more analytic lines:
        # Ticket1 in not invoiced twice and ticket4 is not invoiced
        self.assertEquals(
            self.analines.search(cr, uid, [('name', 'like', 'Invoiced ticket')], count=True), 3)

        # We try to invoice the project itself. It should not do anything
        self.assertRaises(osv.except_osv,
                          self.tickets.create_analytic_line,
                          cr, uid, [project_id])
