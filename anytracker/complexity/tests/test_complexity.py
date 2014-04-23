from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv.orm import except_orm
from os.path import join


class TestComplexity(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestComplexity, cls).initTestData()
        cr, uid = cls.cr, cls.uid
        cls.tickets = cls.registry('anytracker.ticket')
        cls.complexities = cls.registry('anytracker.complexity')
        cls.users = cls.registry('res.users')
        cls.ratings = cls.registry('anytracker.rating')

        cls.complexity2 = cls.ref('anytracker.complexity2')
        cls.complexity3 = cls.ref('anytracker.complexity3')
        cls.complexity4 = cls.ref('anytracker.complexity4')
        cls.member_id = cls.users.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]})
        cls.manager_id = cls.users.create(
            cr, uid,
            {'name': 'Manager',
             'login': 'manager',
             'groups_id': [(6, 0,
                           [cls.ref('base.group_user'),
                            cls.ref('anytracker.group_manager')])]})
        cls.customer_id = cls.users.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_customer')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        method_id = self.ref('anytracker.method_test')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.tickets.create(cr, uid,
                                         {'name': 'test project',
                                          'participant_ids': [(6, 0, participant_ids)],
                                          'method_id': method_id})
        return project_id

    def createLeafTicket(self, name, parent_id):
        cr, uid = self.cr, self.uid
        ticket_id = self.tickets.create(cr, uid,
                                        {'name': name,
                                         'parent_id': parent_id, })
        return ticket_id

    def test_rating(self):
        """ Simple rating scenario: a manager or member can rate, not a customer.
        """
        cr = self.cr
        # create a project with a team of 3 people, and a ticket
        project_id = self.createProject([self.customer_id, self.member_id, self.manager_id])
        ticket_id = self.createLeafTicket('Test simple ticket', project_id)
        # a member can rate
        self.tickets.write(cr, self.member_id, [ticket_id], {'my_rating': self.complexity2})
        # a manager can rate
        self.tickets.write(cr, self.manager_id, [ticket_id], {'my_rating': self.complexity2})
        # a customer cannot rate
        self.assertRaises(except_orm,
                          self.tickets.write,
                          cr, self.customer_id, [ticket_id], {'my_rating': self.complexity2})

    def test_none_rating(self):
        """ Removing ratings linked to a ticket and ensure that this ticket has 0.0 value """
        cr, uid = self.cr, self.uid
        project_id = self.createProject(self.member_id)
        ticket1_id = self.createLeafTicket('Test ticket 1',
                                           project_id)
        self.tickets.write(cr, uid, [ticket1_id],
                           {'my_rating': self.complexity2})
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).rating, 2)
        rating_ids = [r.id for r in self.tickets.browse(cr, uid, ticket1_id).rating_ids if r]
        for rating_id in rating_ids:
            self.tickets.write(cr, uid, [ticket1_id],
                               {'my_rating': None,
                                'rating_ids': [(2, rating_id)]})
        self.assertFalse(self.tickets.browse(cr, uid, ticket1_id).my_rating)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).rating, 0.0)

    def test_compute_rating(self):
        """ Create several tickets for one project. Rate tickets, remove one and
        finally rate ticket with different user.
        Ensure that project's rating and tickets ratings are equal to what we expect"""
        cr = self.cr
        project_id = self.createProject(self.member_id)
        ticket1_id = self.createLeafTicket('Test ticket 1',
                                           project_id)

        self.tickets.write(cr, self.member_id, [ticket1_id],
                           {'my_rating': self.complexity2})
        self.assertEquals(self.tickets.browse(cr, self.member_id, ticket1_id).rating, 2)
        self.assertEquals(self.tickets.browse(cr, self.member_id, project_id).rating, 2)

        ticket2_id = self.createLeafTicket('Test ticket 2', project_id)
        self.tickets.write(cr, self.member_id, [ticket2_id], {'my_rating': self.complexity3})
        self.assertEquals(self.tickets.browse(cr, self.member_id, project_id).rating, 6)
        self.tickets.write(cr, self.member_id, [ticket2_id], {'my_rating': self.complexity2})
        self.assertEquals(self.tickets.browse(cr, self.member_id, project_id).rating, 4)
        # create a subticket under ticket2
        ticket3_id = self.createLeafTicket('Test ticket 3', ticket2_id)
        self.tickets.write(cr, self.member_id, [ticket3_id], {'my_rating': self.complexity4})
        self.assertEquals(self.tickets.browse(cr, self.member_id, project_id).rating, 9)
        self.assertEquals(self.tickets.browse(cr, self.member_id, ticket2_id).rating, 7)

        self.tickets.unlink(cr, self.manager_id, [ticket3_id])
        self.assertEquals(self.tickets.browse(cr, self.member_id, project_id).rating, 2)
        self.assertEquals(self.tickets.browse(cr, self.member_id, ticket2_id).rating, 0)

        # now as manager
        self.tickets.write(cr, self.manager_id, [ticket2_id],
                           {'my_rating': self.complexity4})
        self.assertEquals(self.tickets.browse(cr, self.manager_id, project_id).rating, 6.50)
        self.assertEquals(self.tickets.browse(cr, self.manager_id, ticket2_id).rating, 4.50)

        # test with a risk of 0.0 and 1.0 on the test2 method
        self.tickets.write(cr, self.manager_id, project_id,
                           {'method_id': self.ref('anytracker.method_test2')})
        self.tickets.write(cr, self.member_id, ticket1_id,
                           {'my_rating': self.ref('anytracker.complexity5')})
        self.tickets.write(cr, self.member_id, ticket1_id,
                           {'my_rating': self.ref('anytracker.complexity8')})
        self.tickets.write(cr, self.member_id, ticket1_id,
                           {'my_rating': self.ref('anytracker.complexity7')})
