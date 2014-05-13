# coding: utf-8

from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import osv
from os.path import join


class TestStage(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(self):
        super(TestStage, self).initTestData()
        cr, uid = self.cr, self.uid
        self.ticket_mdl = self.registry('anytracker.ticket')
        self.stage_mdl = self.registry('anytracker.stage')
        self.method_mdl = self.registry('anytracker.method')
        self.user = self.registry('res.users')
        self.rating_mdl = self.registry('anytracker.rating')
        self.member_id = self.user.create(
            cr, uid,
            {'name': 'test member',
             'login': 'test',
             'groups_id': [(6, 0,
                            [self.ref('anytracker.group_member')])]})
        self.customer_id = self.user.create(
            cr, uid, {'name': 'test customer stage',
                      'login': 'test_customer_stage',
                      'groups_id': [(6, 0, [self.ref('anytracker.group_customer')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        test_method = self.ref('anytracker.method_test')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.ticket_mdl.create(cr, uid,
                                            {'name': 'Test',
                                             'participant_ids': [(6, 0, participant_ids)],
                                             'method_id': test_method})
        return project_id

    def createLeafTicket(self, name, parent_id):
        cr, uid = self.cr, self.uid
        ticket_id = self.ticket_mdl.create(cr, uid,
                                           {'name': name,
                                            'parent_id': parent_id, })
        return ticket_id

    def test_move_ticket(self):
        """ Move ticket to a particular stage with different kind of user """
        cr, uid = self.cr, self.uid
        test_method = self.ref('anytracker.method_test')
        project_id = self.createProject([self.member_id, self.customer_id])
        ticket_id = self.createLeafTicket('Ticket to move', project_id)
        todo_stage_id = self.registry('anytracker.stage').create(
            cr, uid, {'name': 'customer todo stage',
                      'method_id': test_method,
                      'state': 'todo',
                      'groups_allowed': [(6, 0, [self.ref('anytracker.group_customer')])]})
        # anytracker member cannot move ticket to this stage
        self.assertRaises(
            osv.except_osv,
            self.ticket_mdl.write,
            cr, self.member_id, [ticket_id], {'stage_id': todo_stage_id})
        # anytracker customer can move ticket to this stage
        self.ticket_mdl.write(cr, self.customer_id, [ticket_id], {'stage_id': todo_stage_id})
        # administrator can move ticket to this stage
        self.ticket_mdl.write(cr, self.customer_id, [ticket_id], {'stage_id': todo_stage_id})
