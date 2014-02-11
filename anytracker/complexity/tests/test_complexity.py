from anybox.testing.openerp import SharedSetupTransactionCase
from datetime import datetime


class TestComplexity(SharedSetupTransactionCase):

    _data_files = ('data.xml', )
    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestComplexity, self).initTestData()
        self.ticket_mdl = self.registry('anytracker.ticket')
        self.complexity_mdl = self.registry('anytracker.complexity')
        self.method_mdl = self.registry('anytracker.method')
        self.user_mdl = self.registry('res.users')
        self.rating_mdl = self.registry('anytracker.rating')

    def createQuickstartProject(self, participant_ids):
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

    def test_compute_rating(self):
        cr, uid = self.cr, self.uid
        complexity_2h = self.ref('anytracker.anytracker_complexity-2h')
        complexity_4h = self.ref('anytracker.anytracker_complexity-4h')
        complexity_1j = self.ref('anytracker.anytracker_complexity-1_jour')
        member_id = self.user_mdl.create(cr, uid,
                                         {'name': 'test member',
                                          'login': 'test',
                                          'groups_id': [(6, 0,
                                                         [self.ref('anytracker.group_member')])]})
        project_id = self.createQuickstartProject(member_id)
        ticket1_id = self.createLeafTicket('Test ticket 1',
                                           project_id)
        self.ticket_mdl.write(cr, uid, [ticket1_id],
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': complexity_2h})],
                               'my_rating': complexity_2h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket1_id).rating, 2)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 2)
        ticket2_id = self.createLeafTicket('Test ticket 2',
                                           project_id)
        self.ticket_mdl.write(cr, uid, [ticket2_id],
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': complexity_4h})],
                               'my_rating': complexity_4h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 6)
        self.ticket_mdl.write(cr, uid, [ticket2_id],
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': complexity_2h})],
                               'my_rating': complexity_2h})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 4)
        ticket3_id = self.createLeafTicket('Test ticket 3',
                                           ticket2_id)
        self.ticket_mdl.write(cr, uid, [ticket3_id],
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': complexity_1j})],
                               'my_rating': complexity_1j})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 11)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket2_id).rating, 9)
        self.ticket_mdl.unlink(cr, uid, [ticket3_id])
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 4)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket2_id).rating, 2)
