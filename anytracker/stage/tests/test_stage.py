# coding: utf-8

from anybox.testing.openerp import SharedSetupTransactionCase


class TestStage(SharedSetupTransactionCase):

    _data_files = ('data.xml', )
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
        quickstart_method = self.ref('anytracker.anytracker_method-quickstart++')
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

    def test_move_to_stage(self):
        cr, uid = self.cr, self.uid
        to_do_stage = self.stage_mdl.search(cr, uid, [('name', '=', u'À faire')])
        rating_stage = self.stage_mdl.search(cr, uid, [('name', '=', u'À évaluer')])
        project_id = self.createProject(self.member_id)
        t1_id = self.createLeafTicket('ticket 1', project_id)
        self.ticket_mdl.write(cr, uid, [t1_id], {'stage_id': to_do_stage[0]})
        self.assertTrue(self.ticket_mdl.browse(cr, uid, t1_id).stage_id, to_do_stage[0])
        self.ticket_mdl.move_to_stage(cr, uid, [t1_id], 'À évaluer')
        self.assertTrue(self.ticket_mdl.browse(cr, uid, t1_id).stage_id, rating_stage[0])
