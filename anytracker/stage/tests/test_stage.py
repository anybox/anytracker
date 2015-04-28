# coding: utf-8

from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import orm
from os.path import join


class TestStage(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(self):
        super(TestStage, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.stages = self.registry('anytracker.stage')
        self.methods = self.registry('anytracker.method')
        self.user = self.registry('res.users')
        self.ratings = self.registry('anytracker.rating')
        self.member_id = self.user.create(
            cr, uid,
            {'name': 'test member',
             'login': 'test',
             'email': 'member@localhost',
             'groups_id': [(6, 0,
                            [self.ref('anytracker.group_member')])]})
        self.customer_id = self.user.create(
            cr, uid, {'name': 'test customer stage',
                      'login': 'test_customer_stage',
                      'groups_id': [(6, 0, [self.ref('anytracker.group_customer')])]})

    def test_move_ticket(self):
        """ Move ticket to a particular stage with different kind of user """
        cr, uid = self.cr, self.uid
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.member_id, self.customer_id])],
             'method_id': self.ref('anytracker.method_test')})
        ticket_id = self.tickets.create(cr, uid,
                                        {'name': 'Ticket to move',
                                         'parent_id': project_id, })
        todo_stage_id = self.registry('anytracker.stage').create(
            cr, uid, {'name': 'customer todo stage',
                      'method_id': self.ref('anytracker.method_test'),
                      'state': 'todo',
                      'groups_allowed': [(6, 0, [self.ref('anytracker.group_customer')])]})
        # anytracker member cannot move ticket to this stage
        self.assertRaises(
            orm.except_orm,
            self.tickets.write,
            cr, self.member_id, [ticket_id], {'stage_id': todo_stage_id})
        # anytracker customer can move ticket to this stage
        self.tickets.write(cr, self.customer_id, [ticket_id], {'stage_id': todo_stage_id})
        # administrator can move ticket to this stage
        self.tickets.write(cr, self.customer_id, [ticket_id], {'stage_id': todo_stage_id})

    def test_enforcements(self):
        cr, uid = self.cr, self.uid
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Test',
             'participant_ids': [(6, 0, [self.member_id])],
             'method_id': self.ref('anytracker.method_test2')})
        ticket_id = self.tickets.create(cr, self.member_id,
                                        {'name': 'Ticket',
                                         'parent_id': project_id, })
        # we try move the ticket to the todo column which forces a rating
        self.assertRaises(
            orm.except_orm,
            self.tickets.write,
            cr, self.member_id, [ticket_id],
            {'stage_id': self.ref('anytracker.stage_test_todo2')})
        # now we first rate red, we should not be able to move the ticket either
        self.tickets.write(
            cr, self.member_id, [ticket_id],
            {'my_rating': self.ref('anytracker.complexity8')})
        self.assertRaises(
            orm.except_orm,
            self.tickets.write,
            cr, self.member_id, [ticket_id],
            {'stage_id': self.ref('anytracker.stage_test_todo2')})
        # now we rate green and it should be ok
        self.tickets.write(
            cr, self.member_id, [ticket_id],
            {'my_rating': self.ref('anytracker.complexity6')})
        self.tickets.write(
            cr, self.member_id, [ticket_id],
            {'stage_id': self.ref('anytracker.stage_test_todo2')})

    def test_progress_on_create_delete(self):
        """ check that the progress is recomputed on ticket creation and deletion
        """
        cr, uid, = self.cr, self.uid
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Project',
             'participant_ids': [(6, 0, [self.member_id, self.customer_id])],
             'method_id': self.ref('anytracker.method_test')})
        ticket1_id = self.tickets.create(cr, uid,
                                         {'name': 'Ticket 1',
                                          'stage_id': self.ref('anytracker.stage_test_todo'),
                                          'parent_id': project_id, })
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).progress, 5.0)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).progress, 5.0)
        # we add a second ticket
        ticket2_id = self.tickets.create(cr, uid,
                                         {'name': 'Ticket 2',
                                          'parent_id': project_id, })
        self.assertEquals(self.tickets.browse(cr, uid, project_id).progress, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).progress, 5.0)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).progress, 1.0)
        # we delete the second ticket
        self.tickets.unlink(cr, uid, ticket2_id)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).progress, 5.0)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).progress, 5.0)
