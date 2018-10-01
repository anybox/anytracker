from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join
from odoo.osv import orm


class TestMethod(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestMethod, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.METHOD = cls.env['anytracker.method']
        cls.STAGE = cls.env['anytracker.stage']
        cls.COMPLEXITY = cls.env['anytracker.complexity']
        USER = cls.env['res.users']

        cls.member_id = USER.create(
            {'name': 'Member',
             'login': 'member',
             'email': 'member@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]}
        ).id
        cls.customer_id = USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'email': 'customer@localhost',
             'groups_id': [(6, 0, [
                 # FIXME: base.group_user actually needed exclusively during u test
                 # for 'mail.activity.mixin' fields with groups='base.group_user'
                 # during ticket write
                 # (in real case ticket is writable without base.group_user)
                 cls.ref('base.group_user'),
                 cls.ref('anytracker.group_customer')])]
            }
        ).id
        cls.manager_id = USER.create(
            {'name': 'Manager',
             'login': 'manager',
             'email': 'manager@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_manager'),
                            cls.ref('account.group_account_user')])]}
        ).id

    def test_method_by_project(self):
        """ Check specific methods for projects
        """
        # we create a project with a team of 3 people
        project = self.TICKET.sudo(self.manager_id).create(
            {'name': 'Test',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             # #11390: analytic journal depreciated on v11
             #'analytic_journal_id':
             #    self.anajournals.sudo(self.manager_id).search([])[0].id,
             'product_id': self.ref('product.product_product_consultant'),
             'method_id': self.ref('anytracker.method_test')})
        # we create a ticket
        ticket = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Invoiced ticket1',
             'parent_id': project.id, })

        # we move the ticket to the todo stage
        ticket.sudo(self.customer_id).write({
            'stage_id': self.ref('anytracker.stage_test_todo')})

        # we customize the method for this specific project
        method = self.METHOD.browse(self.ref('anytracker.method_test')
                                    ).with_context({'project_id': project.id})
        self.assertRaises(
            orm.except_orm, method.sudo(self.customer_id).customize)
        self.assertRaises(
            orm.except_orm, method.sudo(self.member_id).customize)
        new_method = method.sudo(self.manager_id).customize()
        self.assertEquals(ticket.sudo(self.manager_id).method_id, new_method)

        # now we delete the todo stage of the customized method
        new_todo_stage = self.STAGE.sudo(self.manager_id).search([
            ('method_id', '=', new_method.id),
            ('state', '=', 'todo')])[0]
        new_todo_stage.sudo(self.manager_id).unlink()
        self.assertFalse(ticket.sudo(self.manager_id).stage_id.id)

        # now we rate with the new complexity3
        # (supposed to be forbidden in the 'doing' stage)
        # (we actually check that the forbidden complexities
        # have been copied with the method)
        new_cmplx3 = self.COMPLEXITY.sudo(self.member_id).search([
            ('name', '=', 'cmplx3'),
            ('method_id', '=', new_method.id)])[0]
        ticket.sudo(self.member_id).write({'my_rating': new_cmplx3})
        new_doing = self.STAGE.sudo(self.member_id).search([
            ('state', '=', 'doing'),
            ('method_id', '=', new_method.id)])[0]
        self.assertRaises(
            orm.except_orm,
            ticket.sudo(self.member_id).write, {'stage_id': new_doing.id})
