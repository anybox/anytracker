from anybox.testing.openerp import TransactionCase
from datetime import datetime


class TestComplexity(TransactionCase):

    def setUp(self):
        super(TestComplexity, self).setUp()
        self.ticket_mdl = self.registry('anytracker.ticket')
        self.complexity_mdl = self.registry('anytracker.complexity')
        self.method_mdl = self.registry('anytracker.method')
        self.user_mdl = self.registry('res.users')
        self.rating_mdl = self.registry('anytracker.rating')

    def createQuickstartProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        quick_method_id = self.method_mdl.search(cr, uid, [('name', '=', 'Quickstart++')])
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        if not quick_method_id:
            return False
        project_id = self.ticket_mdl.create(cr, uid,
                                            {'name': 'Quickstart test',
                                             'participant_ids': [(6, 0, participant_ids)],
                                             'method_id': quick_method_id[0]})
        return project_id

    def createLeafTicket(self, name, parent_id):
        cr, uid = self.cr, self.uid
        ticket_id = self.ticket_mdl.create(cr, uid,
                                           {'name': name,
                                            'parent_id': parent_id, })
        return ticket_id

    def getComplexityId(self, name):
        cr, uid = self.cr, self.uid
        complexity_id = self.complexity_mdl.search(cr, uid, [('name', '=', name)])
        if not complexity_id:
            return False
        return complexity_id[0]

    def test_compute_rating(self):
        cr, uid = self.cr, self.uid
        complexity_2 = self.getComplexityId('2h')
        complexity_4 = self.getComplexityId('4h')
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
                                                'complexity_id': complexity_2})],
                               'my_rating': complexity_2})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, ticket1_id).rating, 2)
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 2)
        ticket2_id = self.createLeafTicket('Test ticket 2',
                                           project_id)
        self.ticket_mdl.write(cr, uid, [ticket2_id],
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': complexity_4})],
                               'my_rating': complexity_4})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 6)
        self.ticket_mdl.write(cr, uid, [ticket2_id],
                              {'rating_ids': [(0, 0,
                                               {'user_id': 1,
                                                'time': datetime.now(),
                                                'complexity_id': complexity_2})],
                               'my_rating': complexity_2})
        self.assertEquals(self.ticket_mdl.browse(cr, uid, project_id).rating, 4)
