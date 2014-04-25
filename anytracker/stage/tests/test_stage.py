# coding: utf-8

from anybox.testing.openerp import SharedSetupTransactionCase


class TestStage(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestStage, self).initTestData()
        cr, uid = self.cr, self.uid
        self.ticket_mdl = self.registry('anytracker.ticket')
        self.stage_mdl = self.registry('anytracker.stage')
        self.method_mdl = self.registry('anytracker.method')
        self.user = self.registry('res.users')
        self.rating_mdl = self.registry('anytracker.rating')
        self.member_id = self.user.create(cr, uid,
                                          {'name': 'test member',
                                           'login': 'test',
                                           'groups_id': [(6, 0,
                                                          [self.ref('anytracker.group_member')])]})

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
