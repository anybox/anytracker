# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join


class TestStage(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestStage, cls).initTestData()
        cls.tickets = cls.env['anytracker.ticket']
        cls.users = cls.env['res.users']
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.member_id = cls.users.create(
            {'name': 'test member',
             'login': 'test',
             'email': 'test@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member')])]}).id

    def test_delete_assigned_ticket(self):
        """ Check we can delete an assigned ticket (#4171)
        """
        # create a project and a ticket
        project = self.tickets.create({
            'name': 'Test',
            'participant_ids': [(6, 0, [self.member_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.tickets.create({
            'name': 'test assign',
            'parent_id': project.id})
        # assign the ticket to the user
        ticket.write({'assigned_user_id': self.member_id})
        # check the user is assigned
        self.assertEquals(ticket.assigned_user_id.id, self.member_id)
        # Check we can delete the ticket
        ticket.unlink()

    def test_unassign(self):
        """ Check we can unassign a ticket
        """
        # create a project and a ticket
        project = self.tickets.create({
            'name': 'Test',
            'participant_ids': [(6, 0, [self.member_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.tickets.create({
            'name': 'test assign',
            'parent_id': project.id})
        # assign the ticket to the user
        ticket.write({'assigned_user_id': self.member_id})
        # check the user is assigned
        self.assertEquals(ticket.assigned_user_id.id, self.member_id)
        # check we can unassign
        ticket.write({'assigned_user_id': False})
        self.assertEquals(ticket.assigned_user_id.id, False)
