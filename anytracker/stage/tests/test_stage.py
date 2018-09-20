# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase
from odoo.osv import orm
from os.path import join


class TestStage(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestStage, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.STAGE = cls.env['anytracker.stage']
        USER = cls.env['res.users']
        cls.member_id = USER.create({
            'name': 'test member',
            'login': 'test',
            'email': 'member@localhost',
            'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member')])]}
        ).id
        cls.customer_id = USER.create(
            {'name': 'test customer stage',
             'login': 'test_customer_stage',
             'groups_id': [(6, 0, [cls.ref('anytracker.group_customer')])]}
        ).id

    def test_move_ticket(self):
        """ Move ticket to a particular stage with different kind of user """
        project = self.TICKET.create({
            'name': 'Test',
            'participant_ids': [(6, 0, [self.member_id, self.customer_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.TICKET.create({
            'name': 'Ticket to move',
            'parent_id': project.id, })
        todo_stage = self.STAGE.create({
            'name': 'customer todo stage',
            'method_id': self.ref('anytracker.method_test'),
            'state': 'todo',
            'groups_allowed':
                [(6, 0, [self.ref('anytracker.group_customer')])]})
        # anytracker member cannot move ticket to this stage
        self.assertRaises(
            orm.except_orm,
            ticket.sudo(self.member_id).write, {'stage_id': todo_stage.id})
        # anytracker customer can move ticket to this stage
        ticket.sudo(self.customer_id).write({'stage_id': todo_stage.id})
        # administrator can move ticket to this stage
        ticket.sudo().write({'stage_id': todo_stage.id})

    def test_enforcements(self):
        project = self.TICKET.create(
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.member_id])],
             'method_id': self.ref('anytracker.method_test2')})
        ticket = self.TICKET.sudo(self.member_id).create({
            'name': 'Ticket',
            'parent_id': project.id})
        # we try move the ticket to the todo column which forces a rating
        self.assertRaises(
            orm.except_orm,
            ticket.sudo(self.member_id).write,
            {'stage_id': self.ref('anytracker.stage_test_todo2')})
        # now we first rate red, we should'nt be able to move the ticket either
        ticket.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity8')})
        self.assertRaises(
            orm.except_orm,
            ticket.sudo(self.member_id).write,
            {'stage_id': self.ref('anytracker.stage_test_todo2')})
        # now we rate green and it should be ok
        ticket.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity6')})
        ticket.sudo(self.member_id).write({
            'stage_id': self.ref('anytracker.stage_test_todo2')})

    def test_progress_on_create_delete(self):
        """ check that the progress is recomputed on ticket creation and deletion
        """
        project = self.TICKET.create(
            {'name': 'Project',
             'participant_ids': [(6, 0, [self.member_id, self.customer_id])],
             'method_id': self.ref('anytracker.method_test')})
        ticket1 = self.TICKET.create({
            'name': 'Ticket 1',
            'stage_id': self.ref('anytracker.stage_test_todo'),
            'parent_id': project.id, })
        self.assertEquals(ticket1.progress, 5.0)
        self.assertEquals(project.progress, 5.0)
        # we add a second ticket
        ticket2 = self.TICKET.create({
            'name': 'Ticket 2',
            'parent_id': project.id, })
        self.assertEquals(project.progress, 3.0)
        self.assertEquals(ticket1.progress, 5.0)
        self.assertEquals(ticket2.progress, 1.0)
        # we delete the second ticket
        ticket2.unlink()
        self.assertEquals(ticket1.progress, 5.0)
        self.assertEquals(project.progress, 5.0)

    def test_create_node(self):
        """ticket 7089"""
        project = self.TICKET.create(
            {'name': 'Ticket7089 bug project',
             'participant_ids': [(6, 0, [self.member_id, self.customer_id])],
             'method_id': self.ref('anytracker.method_test')})
        self.TICKET.create(
            {'name': 'Ticket7089 bug node',
             'type': self.ref('anytracker.anytracker_ticket_type_project'),
             'parent_id': project.id,
             'participant_ids': [(6, 0, [self.member_id, self.customer_id])],
             'method_id': self.ref('anytracker.method_test')})
