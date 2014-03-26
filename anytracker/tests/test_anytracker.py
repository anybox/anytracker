from anybox.testing.openerp import SharedSetupTransactionCase


class TestAnytracker(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestAnytracker, self).initTestData()
        cr, uid = self.cr, self.uid
        self.ticket_mdl = self.registry('anytracker.ticket')
        self.user = self.registry('res.users')

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

    def test_name_search(self):
        """
            Test the name_search function in anytracker.ticket module.
            We may be able to find a ticket from his name or number
        """
        cr, uid = self.cr, self.uid
        # Create a ticket
        project_id = self.createProject([self.customer_id, self.member_id, self.manager_id])
        ticket_id = self.createLeafTicket('Test simple ticket', project_id)
        # get his number
        ticket_number = self.ticket_mdl.read(cr, uid, ticket_id, ['number'])['number']
        # Search by name
        ticket_id_by_name = self.ticket_mdl.search(cr, uid, [('name', '=', 'Test simple ticket')])

        # Search by ticket number
        ticket_id_by_number = self.ticket_mdl.search(cr, uid, [('number', '=', ticket_number)])
        # Check if the two ids are equals
        self.assertEquals(ticket_id_by_name[0], ticket_id_by_number[0])
