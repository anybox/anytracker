from anybox.testing.openerp import SharedSetupTransactionCase
from odoo.exceptions import except_orm
from os.path import join


class TestComplexity(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestComplexity, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.RATING = cls.env['anytracker.rating']

        cls.complexity2 = cls.ref('anytracker.complexity2')
        cls.complexity3 = cls.ref('anytracker.complexity3')
        cls.complexity4 = cls.ref('anytracker.complexity4')

        USER = cls.env['res.users']

        recset = USER.search([('login', '=', 'member')])
        cls.member_id = recset and recset[0].id or USER.create(
            {'name': 'Member',
             'login': 'member',
             'email': 'member@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]}
        ).id

        recset = USER.search([('login', '=', 'manager')])
        cls.manager_id = recset and recset[0].id or USER.create(
            {'name': 'Manager',
             'login': 'manager',
             'email': 'manager@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('base.group_user'),
                            cls.ref('anytracker.group_manager')])]}
        ).id

        recset = USER.search([('login', '=', 'partner')])
        cls.partner_id = recset and recset[0].id or USER.create(
            {'name': 'Partner',
             'login': 'partner',
             'email': 'partner@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_partner')])]}
        ).id

        recset = USER.search([('login', '=', 'customer')])
        cls.customer_id = recset and recset[0].id or USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'email': 'customer@localhost',
             'groups_id': [(6, 0, [
                   # FIXME: base.group_user actually needed exclusively during u test
                   # for 'mail.activity.mixin' fields with groups='base.group_user'
                   # during ticket write
                   # (in real case ticket is writable without base.group_user)
                   cls.ref('base.group_user'),
                   cls.ref('anytracker.group_customer')])]}
        ).id

    def test_rating(self):
        """ Simple rating scenario: a manager or member or partner can rate,
        not a customer.
        """
        # create a project with a team of 4 people, and a ticket
        project = self.TICKET.create({
            'name': 'test project',
            'participant_ids': [(6, 0, [
                self.customer_id, self.partner_id,
                self.member_id, self.manager_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.TICKET.create({
            'name': 'Test simple ticket',
            'parent_id': project.id})
        # a member can rate
        ticket.sudo(self.member_id).write({'my_rating': self.complexity2})
        # a partner can rate
        ticket.sudo(self.partner_id).write({'my_rating': self.complexity2})
        # a manager can rate
        ticket.sudo(self.manager_id).write({'my_rating': self.complexity2})
        # a customer cannot rate
        self.assertRaises(
            except_orm,
            ticket.sudo(self.customer_id).write,
            {'my_rating': self.complexity2})

    def test_none_rating(self):
        """ Removing ratings linked to a ticket
        and ensure that this ticket has 0.0 value
        """
        project = self.TICKET.create({
            'name': 'test project',
            'participant_ids': [(6, 0, [self.member_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket1 = self.TICKET.create({
            'name': 'Test ticket 1',
            'parent_id': project.id})
        ticket1.write({'my_rating': self.complexity2})
        self.assertEquals(ticket1.rating, 2)
        # add a rating None from another person, and check it is ignored
        ticket1.write({'my_rating': None})
        self.assertFalse(ticket1.my_rating)
        self.assertEquals(ticket1.rating, 0.0)
        ticket1.sudo(self.member_id).write({'my_rating': self.complexity2})
        self.assertEquals(ticket1.rating, 2)

    def test_compute_rating(self):
        """ Create several tickets for one project. Rate tickets, remove one and
        finally rate ticket with different user.
        Ensure that project's rating and tickets ratings are correct
        """
        project = self.TICKET.create(
            {'name': 'test project',
             'participant_ids': [(6, 0, [self.member_id])],
             'method_id': self.ref('anytracker.method_test')})
        ticket1 = self.TICKET.create({
            'name': 'Test ticket 1',
            'parent_id': project.id})

        ticket1.sudo(self.member_id).write({'my_rating': self.complexity2})
        self.assertEquals(ticket1.sudo(self.member_id).rating, 2)
        self.assertEquals(project.sudo(self.member_id).rating, 2)

        ticket2 = self.TICKET.create({
            'name': 'Test ticket 2',
            'parent_id': project.id})
        ticket2.sudo(self.member_id).write({'my_rating': self.complexity3})
        self.assertEquals(project.sudo(self.member_id).rating, 6)
        ticket2.sudo(self.member_id).write({'my_rating': self.complexity2})
        self.assertEquals(project.sudo(self.member_id).rating, 4)
        # create a subticket under ticket2
        ticket3 = self.TICKET.create({
            'name': 'Test ticket 3',
            'parent_id': ticket2.id})
        ticket3.sudo(self.member_id).write({'my_rating': self.complexity4})
        self.assertEquals(project.sudo(self.member_id).rating, 9)
        self.assertEquals(ticket2.sudo(self.member_id).rating, 7)

        ticket3.sudo(self.manager_id).unlink()
        self.assertEquals(project.sudo(self.member_id).rating, 2)
        self.assertEquals(ticket2.sudo(self.member_id).rating, 0)

        # now as manager
        ticket2.sudo(self.manager_id).write({'my_rating': self.complexity4})
        self.assertEquals(project.sudo(self.manager_id).rating, 2)
        self.assertEquals(ticket2.sudo(self.manager_id).rating, 0)

        # test with a risk of 0.0 and 1.0 on the test2 method
        project.sudo(self.manager_id).write({
            'method_id': self.ref('anytracker.method_test2')})
        ticket1.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity5')})
        ticket1.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity8')})
        ticket1.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity7')})

    def test_get_complexity_color(self):
        """ test the color of tickets
        """
        project = self.TICKET.create({
            'name': 'test project',
            'participant_ids': [(6, 0, [self.member_id])],
            'method_id': self.ref('anytracker.method_test2')})
        ticket1 = self.TICKET.create({
            'name': 'Test ticket 1',
            'parent_id': project.id})
        # we give two complexities
        ticket1.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity6')})
        ticket1.sudo(self.manager_id).write({
            'my_rating': self.ref('anytracker.complexity7')})
        # check the computed rating and risk
        self.assertEquals(ticket1.sudo(self.member_id).rating, 3.5)
        self.assertEquals(project.sudo(self.member_id).risk, 0.357738371066744)
        # the computed color should be 3 (complexity7)
        self.assertEquals(ticket1.sudo(self.member_id).color, 'orange')
        # add a risky complexity
        ticket1.sudo(self.manager_id).write({
            'my_rating': self.ref('anytracker.complexity8')})
        self.assertEquals(ticket1.sudo(self.member_id).risk, 1.0)
        self.assertEquals(ticket1.sudo(self.member_id).color, 'red')

    def test_rate_at_creation(self):
        """ check that a ticket rated at creation has a rating
        """
        project = self.TICKET.create(
            {'name': 'test project',
             'participant_ids': [(6, 0, [self.member_id])],
             'method_id': self.ref('anytracker.method_test2')})
        ticket1 = self.TICKET.create({
            'name': 'Test ticket 1',
            'parent_id': project.id,
            'my_rating': self.ref('anytracker.complexity7')})
        self.assertEquals(ticket1.sudo(self.member_id).rating, 4.5)
