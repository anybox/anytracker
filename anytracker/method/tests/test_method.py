from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join
from openerp.osv import orm


class TestInvoicing(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(self):
        super(TestInvoicing, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.methods = self.registry('anytracker.method')
        self.stages = self.registry('anytracker.stage')
        self.complexities = self.registry('anytracker.complexity')
        self.users = self.registry('res.users')
        self.anajournals = self.registry('account.analytic.journal')

        self.member_id = self.users.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'email': 'member@localhost',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_member'),
                            self.ref('base.group_user')])]})
        self.customer_id = self.users.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'email': 'customer@localhost',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_customer')])]})

        self.manager_id = self.users.create(
            cr, uid,
            {'name': 'Manager',
             'login': 'manager',
             'email': 'manager@localhost',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_manager'),
                            self.ref('account.group_account_user')])]})

    def test_method_by_project(self):
        """ Check created analytic lines from a ticket
        """
        cr = self.cr
        # we create a project with a team of 3 people
        project_id = self.tickets.create(
            cr, self.manager_id,
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'analytic_journal_id': self.anajournals.search(cr, self.manager_id, [])[0],
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': self.ref('anytracker.method_test')})
        # we create a ticket
        ticket_id = self.tickets.create(
            cr, self.customer_id,
            {'name': 'Invoiced ticket1',
             'parent_id': project_id, })

        # we move the ticket to the todo stage
        self.tickets.write(
            cr, self.customer_id, ticket_id,
            {'stage_id': self.ref('anytracker.stage_test_todo')})

        # we customize the method for this specific project
        self.assertRaises(
            orm.except_orm,
            self.methods.customize,
            cr, self.customer_id, self.ref('anytracker.method_test'),
            context={'project_id': project_id})
        self.assertRaises(
            orm.except_orm,
            self.methods.customize,
            cr, self.member_id, self.ref('anytracker.method_test'),
            context={'project_id': project_id})
        new_method_id = self.methods.customize(
            cr, self.manager_id, self.ref('anytracker.method_test'),
            context={'project_id': project_id})
        project_method_id = self.tickets.browse(cr, self.manager_id, project_id).method_id.id
        self.assertEquals(project_method_id, new_method_id)

        # now we delete the todo stage of the customized method
        new_todo_stage_id = self.stages.search(
            cr, self.manager_id, [('method_id', '=', new_method_id),
                                  ('state', '=', 'todo')])[0]
        self.stages.unlink(cr, self.manager_id, new_todo_stage_id)
        self.assertFalse(self.tickets.browse(cr, self.manager_id, ticket_id).stage_id)

        # now we rate with the new complexity3 (supposed to be forbidden in the 'doing' stage)
        # (we actually check that the forbidden complexities have been copied with the method)
        new_cmplx3 = self.complexities.search(
            cr, self.member_id, [('name', '=', 'cmplx3'),
                                 ('method_id', '=', new_method_id)])[0]
        self.tickets.write(cr, self.member_id, ticket_id, {'my_rating': new_cmplx3})
        new_doing = self.stages.search(
            cr, self.member_id, [('state', '=', 'doing'),
                                 ('method_id', '=', new_method_id)])[0]
        self.assertRaises(
            orm.except_orm,
            self.tickets.write,
            cr, self.member_id, ticket_id,
            {'stage_id': new_doing})
