from anybox.testing.openerp import SharedSetupTransactionCase
from datetime import datetime
from openerp.osv.orm import except_orm


class TestComplexity(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestComplexity, self).initTestData()
        cr, uid = self.cr, self.uid
        self.ticket_mdl = self.registry('anytracker.ticket')
        self.complexity_mdl = self.registry('anytracker.complexity')
        self.user = self.registry('res.users')
        self.rating_mdl = self.registry('anytracker.rating')

        self.complexity_2h = self.ref('anytracker.anytracker_complexity-2h')
        self.complexity_4h = self.ref('anytracker.anytracker_complexity-4h')
        self.complexity_1j = self.ref('anytracker.anytracker_complexity-1_jour')

        self.user_id = self.user.create(cr, uid,
                                        {'name': 'test member',
                                         'login': 'test',  # FIXME: choose a more explicit login
                                         'groups_id': [(6, 0,  # FIXME: manager or member?
                                                        [self.ref('anytracker.group_member'),
                                                         self.ref('base.group_user'),
                                                         self.ref('anytracker.group_manager')])]})
        self.user2_id = self.user.create(cr, uid,
                                         {'name': 'test member 2',
                                          'login': 'test2',
                                          'groups_id': [(6, 0,  # FIXME: manager or member?
                                                         [self.ref('anytracker.group_member'),
                                                          self.ref('base.group_user'),
                                                          self.ref('anytracker.group_manager')])]})
        self.member_id = self.user.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_member'),
                            self.ref('base.group_user')])]})
        self.manager_id = self.user.create(
            cr, uid,
            {'name': 'Manager',
             'login': 'manager',
             'groups_id': [(6, 0,
                          [self.ref('base.group_user'),
                           self.ref('anytracker.group_manager')])]})
        self.customer_id = self.user.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_customer')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        quickstart_method = self.ref('anytracker.anytracker_method-quickstart')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.ticket_mdl.create(cr, uid,
                                            {'name': 'Quickstart test',
                                             'participant_ids': [(6, 0, participant_ids)],
                                             'method_id': quickstart_method})
        return project_id

    def createLeafTicket(self, name, parent_id):
        cr, uid = self.cr, self.uid
        ticket_id = self.ticket_mdl.create(cr, uid,
                                           {'name': name,
                                            'parent_id': parent_id, })
        return ticket_id

    def test_rating(self):
        """ Simple rating scenario: a manager or member can rate, not a customer.
        """
        cr, uid = self.cr, self.uid
        # create a project with a team of 3 people
        project_id = self.createProject([self.customer_id, self.member_id, self.manager_id])
        # create a ticket
        ticket_id = self.createLeafTicket('Test simple ticket', project_id)
        # a member can rate
        self.ticket_mdl.write(cr, self.member_id, [ticket_id], {'my_rating': 1})
        # a manager can rate
        self.ticket_mdl.write(cr, self.manager_id, [ticket_id], {'my_rating': 2})
        # a customer cannot rate
        self.assertRaises(except_orm,
                          self.ticket_mdl.write,
                          cr, self.customer_id, [ticket_id], {'my_rating': 3})

    def test_none_rating(self):
        # FIXME: docstring + comments
        cr, uid = self.cr, self.uid
        project_id = self.createProject(self.user_id)
        ticket1_id = self.createLeafTicket('Test ticket 1',
                                           project_id)
        self.ticket_mdl.write(cr, uid, [ticket1_id],  # FIXME: no need to write 'rating_ids'
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': self.complexity_2h})],
                               'my_rating': self.complexity_2h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket1_id).rating, 2)
        rating_ids = [r.id for r in self.ticket_mdl.browse(cr, uid, ticket1_id).rating_ids if r]
        for rating_id in rating_ids:
            self.ticket_mdl.write(cr, uid, [ticket1_id],
                                  {'my_rating': None,
                                   'rating_ids': [(2, rating_id)]})
        self.assertFalse(self.ticket_mdl.browse(cr, uid, ticket1_id).my_rating)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket1_id).rating, 0.0)

    def test_compute_rating(self):
        # FIXME: docstring + comments
        cr, uid = self.cr, self.uid
        project_id = self.createProject(self.user_id)
        ticket1_id = self.createLeafTicket('Test ticket 1',
                                           project_id)
        uid = self.user_id
        self.ticket_mdl.write(cr, uid, [ticket1_id],  # FIXME: no need to write 'rating_ids'
                              {'rating_ids': [(0, 0,
                                               {'user_id': self.user_id,
                                                'time': datetime.now(),
                                                'complexity_id': self.complexity_2h})],
                               'my_rating': self.complexity_2h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket1_id).rating, 2)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 2)
        ticket2_id = self.createLeafTicket('Test ticket 2',
                                           project_id)
        self.ticket_mdl.write(cr, uid, [ticket2_id],  # FIXME: no need to write 'rating_ids'
                              {'rating_ids': [(0, 0,
                                               {'user_id': self.user_id,
                                                'time': datetime.now(),
                                                'complexity_id': self.complexity_4h})],
                               'my_rating': self.complexity_4h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 6)
        self.ticket_mdl.write(cr, uid, [ticket2_id],  # FIXME: no need to write 'rating_ids'
                              {'rating_ids': [(0, 0,
                                               {'user_id': self.user_id,
                                                'time': datetime.now(),
                                                'complexity_id': self.complexity_2h})],
                               'my_rating': self.complexity_2h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 4)
        ticket3_id = self.createLeafTicket('Test ticket 3',
                                           ticket2_id)
        self.ticket_mdl.write(cr, uid, [ticket3_id],  # FIXME: no need to write 'rating_ids'
                              {'rating_ids': [(0, 0,
                                               {'user_id': self.user_id,
                                                'time': datetime.now(),
                                                'complexity_id': self.complexity_1j})],
                               'my_rating': self.complexity_1j})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 11)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket2_id).rating, 9)
        self.ticket_mdl.unlink(cr, uid, [ticket3_id])
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 4)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket2_id).rating, 2)
        uid = self.user2_id
        self.ticket_mdl.write(cr, uid, [ticket2_id],  # FIXME: no need to write 'rating_ids'
                              {'rating_ids': [(0, 0,
                                               {'user_id': self.user2_id,
                                                'time': datetime.now(),
                                                'complexity_id': self.complexity_1j})],
                               'my_rating': self.complexity_1j})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 6.50)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket2_id).rating, 4.50)
