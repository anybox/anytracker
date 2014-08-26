# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join


class TestStage(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(self):
        super(TestStage, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.users = self.registry('res.users')
        self.assignment = self.registry('anytracker.assignment')
        self.member_id = self.users.create(cr, uid,
                                           {'name': 'test member',
                                            'login': 'test',
                                            'groups_id': [(6, 0,
                                                          [self.ref('anytracker.group_member')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        test_method = self.ref('anytracker.method_test')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.tickets.create(cr, uid,
                                         {'name': 'Test',
                                          'participant_ids': [(6, 0, participant_ids)],
                                          'method_id': test_method})
        return project_id

    def createLeafTicket(self, name, parent_id):
        cr, uid = self.cr, self.uid
        ticket_id = self.tickets.create(cr, uid,
                                        {'name': name,
                                         'parent_id': parent_id, })
        return ticket_id

    def test_get_all_subtickets_ids(self):
        """ Check we get the right ids list """
        cr, uid = self.cr, self.uid
        # create a project and a ticket
        parent_ticket_id = self.createLeafTicket('Test subtickets',
                                                 self.createProject([self.member_id]))
        # create 3 subtickets to the previous one
        first_child_id = self.createLeafTicket('child 1', parent_ticket_id)
        second_child_id = self.createLeafTicket('child 2', parent_ticket_id)
        third_child_id = self.createLeafTicket('child 3', parent_ticket_id)

        ticket_ids = self.tickets.get_all_subtickets_ids(
            cr, uid, self.tickets.browse(cr, uid, parent_ticket_id))
        self.assertEquals(ticket_ids, [first_child_id, second_child_id, third_child_id])

    def test_delete_assigned_ticket(self):
        """ Check we can delete an assigned ticket (#4171)
        """
        cr, uid = self.cr, self.uid
        # create a project and a ticket
        ticket_id = self.createLeafTicket('test assign', self.createProject([self.member_id]))
        # assign the ticket to the user
        self.tickets.write(cr, uid, ticket_id, {'assigned_user_id': self.member_id})
        # check the user is assigned
        assigned_user_id = self.tickets.browse(cr, uid, ticket_id).assigned_user_id.id
        self.assertEquals(assigned_user_id, self.member_id)
        # Check we can delete the ticket
        self.tickets.unlink(cr, uid, [ticket_id])

    def test_unassign(self):
        """ Check we can unassign a ticket
        """
        cr, uid = self.cr, self.uid
        # create a project and a ticket
        ticket_id = self.createLeafTicket('test assign', self.createProject([self.member_id]))
        # assign the ticket to the user
        self.tickets.write(cr, uid, ticket_id, {'assigned_user_id': self.member_id})
        # check the user is assigned
        assigned_user_id = self.tickets.browse(cr, uid, ticket_id).assigned_user_id.id
        self.assertEquals(assigned_user_id, self.member_id)
        # check we can unassign
        self.tickets.write(cr, uid, ticket_id, {'assigned_user_id': False})
        assigned_user_id = self.tickets.browse(cr, uid, ticket_id).assigned_user_id.id
        self.assertEquals(assigned_user_id, False)
