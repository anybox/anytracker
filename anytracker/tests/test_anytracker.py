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

    def test_name_search(self):
        """
            Test the name_search function in anytracker.ticket module.
            We may be able to find a ticket from his name or number
        """
        cr, uid = self.cr, self.uid
        # Create a ticket
        project_id = self.ticket_mdl.create(
            cr, uid,
            {'name': 'Quickstart test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.anytracker_method-quickstart')})
        ticket_id = self.ticket_mdl.create(
            cr, uid, {'name': 'Test simple ticket', 'parent_id': project_id, })
        # get his number
        ticket_number = self.ticket_mdl.read(cr, uid, ticket_id, ['number'])['number']
        # Search by name
        ticket_id_by_name = self.ticket_mdl.search(cr, uid, [('name', '=', 'Test simple ticket')])

        # Search by ticket number
        ticket_id_by_number = self.ticket_mdl.search(cr, uid, [('number', '=', ticket_number)])
        # Check if the two ids are equals
        self.assertEquals(ticket_id_by_name[0], ticket_id_by_number[0])

    def test_disable_project(self):
        """ Set a node as inactive, and check all subtickets are also inactive
        """
        cr, uid = self.cr, self.uid
        # create a project
        project_id = self.ticket_mdl.create(
            cr, uid,
            {'name': 'Quickstart test2',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.anytracker_method-quickstart')})
        # create a sub node and 2 tickets
        node_id = self.ticket_mdl.create(cr, uid, {'name': 'A node', 'parent_id': project_id, })
        self.ticket_mdl.create(cr, uid, {'name': 'ticket1', 'parent_id': node_id, })
        self.ticket_mdl.create(cr, uid, {'name': 'ticket2', 'parent_id': node_id, })
        # check that we can find all the tickets of the project
        self.assertEquals(
            4, self.ticket_mdl.search(cr, uid, [('id', 'child_of', project_id)], count=True))
        # set the project as inactive
        self.ticket_mdl.write(cr, uid, project_id, {'active': False})
        # check that we CANNOT find all the tickets of the project
        self.assertEquals(
            0, self.ticket_mdl.search(cr, uid, [('id', 'child_of', project_id)], count=True))
        # set the project as active again
        self.ticket_mdl.write(cr, uid, project_id, {'active': True})
        # check that we can find again all the tickets of the project
        self.assertEquals(
            4, self.ticket_mdl.search(cr, uid, [('id', 'child_of', project_id)], count=True))
