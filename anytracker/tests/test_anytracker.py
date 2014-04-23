from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv.orm import except_orm
import base64


class TestAnytracker(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = ('data.xml',)

    @classmethod
    def initTestData(self):
        super(TestAnytracker, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.attachments = self.registry('ir.attachment')
        self.users = self.registry('res.users')
        self.partners = self.registry('res.partner')

        self.member_id = self.users.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_member'),
                            self.ref('base.group_user')])]})
        self.manager_id = self.users.create(
            cr, uid,
            {'name': 'Manager',
             'login': 'manager',
             'groups_id': [(6, 0,
                           [self.ref('base.group_user'),
                            self.ref('anytracker.group_manager')])]})
        self.customer_id = self.users.create(
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
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Quickstart test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_quickstart')})
        ticket_id = self.tickets.create(
            cr, uid, {'name': 'Test simple ticket', 'parent_id': project_id, })

        # get his number
        ticket_number = self.tickets.read(cr, uid, ticket_id, ['number'])['number']

        # Search by name
        ticket_id_by_name = self.tickets.search(cr, uid, [('name', '=', 'Test simple ticket')])

        # Search by ticket number
        ticket_id_by_number = self.tickets.search(cr, uid, [('name', '=', ticket_number)])

        # Check result
        for i in range(len(ticket_id_by_name)):
            self.assertEquals(ticket_id_by_name[i], ticket_id)

        for j in range(len(ticket_id_by_number)):
            self.assertEquals(ticket_id_by_number[j], ticket_id)

    def test_disable_project(self):
        """ Set a node as inactive, and check all subtickets are also inactive
        """
        cr, uid = self.cr, self.uid
        # create a project
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Quickstart test2',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_quickstart')})
        # create a sub node and 2 tickets
        node_id = self.tickets.create(cr, uid, {'name': 'A node', 'parent_id': project_id, })
        self.tickets.create(cr, uid, {'name': 'ticket1', 'parent_id': node_id, })
        self.tickets.create(cr, uid, {'name': 'ticket2', 'parent_id': node_id, })
        # check that we can find all the tickets of the project
        self.assertEquals(
            4, self.tickets.search(cr, uid, [('id', 'child_of', project_id)], count=True))
        # set the project as inactive
        self.tickets.write(cr, uid, project_id, {'active': False})
        # check that we CANNOT find all the tickets of the project
        self.assertEquals(
            0, self.tickets.search(cr, uid, [('id', 'child_of', project_id)], count=True))
        # set the project as active again
        self.tickets.write(cr, uid, project_id, {'active': True})
        # check that we can find again all the tickets of the project
        self.assertEquals(
            4, self.tickets.search(cr, uid, [('id', 'child_of', project_id)], count=True))

    def test_attachments(self):
        """ Check attachment creation, deletion and access
        """
        cr, uid = self.cr, self.uid
        # create two projects, one with customer, on without
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Attachment test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_maintenance')})
        # let the customer create a ticket and an attachment
        ticket_id = self.tickets.create(cr, self.customer_id,
                                        {'name': 'A ticket', 'parent_id': project_id, })
        attach1_id = self.attachments.create(cr, self.customer_id, {
            'name': 'testfile',
            'db_datas': base64.b64encode('0000'),
            'datas_fname': 'testfile',
            'res_model': 'anytracker.ticket',
            'res_id': ticket_id,
        })
        # don't let the customer delete his attachment
        self.assertRaises(except_orm, self.attachments.unlink, cr, self.customer_id, [attach1_id])
        # check that the customer cannot access an attachment of another project
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Attachment test2',
             'participant_ids': [(6, 0, [self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_maintenance')})
        ticket_id = self.tickets.create(cr, self.member_id,
                                        {'name': 'A ticket2', 'parent_id': project_id, })
        attach2_id = self.attachments.create(cr, self.member_id, {
            'name': 'testfile2',
            'db_datas': base64.b64encode('1111'),
            'datas_fname': 'testfile2',
            'res_model': 'anytracker.ticket',
            'res_id': ticket_id,
        })
        attach_ids = self.attachments.search(cr, self.customer_id,
                                             [('id', 'in', (attach1_id, attach2_id))])
        self.assertEquals(attach_ids, [attach1_id])
        self.assertRaises(except_orm,
                          self.attachments.read, cr, self.customer_id, [attach2_id], ['name'])

    def test_customer_access(self):
        """ Protect sensitive data
        """
        cr, uid = self.cr, self.uid
        project_id = self.tickets.create(
            cr, uid,
            {'name': 'Partner access test',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_maintenance')})
        # create a partner as manager
        partner_id = self.partners.create(cr, 1, {
            'name': 'test partner', 'email': 'test@example.com'})
        # customer cannot search or access partners
        partner_ids = self.partners.search(cr, self.customer_id, [])
        self.assertTrue(len(partner_ids) == 3)
        self.assertRaises(except_orm,
                          self.partners.read, cr, self.customer_id, (partner_id,), ['name'])
        self.assertRaises(except_orm,
                          self.partners.read, cr, self.customer_id, (partner_id,), ['email'])

        # users are protected as well
        user_ids = self.partners.search(cr, self.customer_id, [])
        self.assertTrue(len(user_ids) == 3)
        # The customer can access the member user
        member_partner_id = self.users.read(cr, self.customer_id, [self.member_id],
                                            ['name', 'partner_id'])[0]['partner_id'][0]
        self.partners.read(cr, self.customer_id, [member_partner_id], ['email'])
        # But not if the member is no more in the project
        self.tickets.write(cr, uid, [project_id], {'participant_ids': [(3, self.member_id)]})
        self.assertRaises(except_orm,
                          self.partners.read, cr, self.customer_id, [member_partner_id], ['email'])

    def test_move_tickets(self):
        """ Check that we can move a ticket to another node or project
        and that everything is still consistent
        """
        cr, uid = self.cr, self.uid
        # create a first project with 3 tickets
        project_id = self.tickets.create(
            cr, self.manager_id,
            {'name': 'Project1',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 0.0)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.5)

        node_id = self.tickets.create(cr, self.customer_id,
                                      {'name': 'Node1', 'parent_id': project_id, })
        self.assertEquals(self.tickets.browse(cr, uid, node_id).rating, 0.0)
        self.assertEquals(self.tickets.browse(cr, uid, node_id).risk, 0.5)
        ticket1_id = self.tickets.create(cr, self.customer_id,
                                         {'name': 'Ticket1', 'parent_id': node_id, })
        ticket2_id = self.tickets.create(cr, self.customer_id,
                                         {'name': 'Ticket2', 'parent_id': node_id, })

        # rate the tickets and set the stage
        self.tickets.write(cr, self.member_id, ticket1_id,
                           {'my_rating': self.ref('anytracker.complexity1')})
        # I change my mind and set another complexity
        self.tickets.write(cr, self.member_id, ticket1_id, {
            'my_rating': self.ref('anytracker.complexity2'),
            'stage_id': self.ref('anytracker.stage_test_todo'),
            })
        self.tickets.write(cr, self.member_id, ticket2_id, {
            'my_rating': self.ref('anytracker.complexity4'),
            'stage_id': self.ref('anytracker.stage_test_doing'),
            })
        # the manager also rates the tickets
        self.tickets.write(cr, self.manager_id, ticket1_id,
                           {'my_rating': self.ref('anytracker.complexity3')})
        self.tickets.write(cr, self.manager_id, ticket2_id,
                           {'my_rating': self.ref('anytracker.complexity3')})

        # check the progress and risk
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).rating, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).risk, 0.307179676972449)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).rating, 5.5)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).risk, 0.452277442494834)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 8.5)
        # 1-((1-0.307179676972449)*(1-0.452277442494834))**(1/2.) = 0.383985942351795
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.383985942351795)
        self.assertEquals(self.tickets.browse(cr, uid, node_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, node_id).risk, 0.383985942351795)

        # Now create a second empty node
        node2_id = self.tickets.create(cr, self.member_id,
                                       {'name': 'Node2', 'parent_id': project_id})
        self.assertEquals(self.tickets.browse(cr, uid, node2_id).rating, 0.0)
        self.assertEquals(self.tickets.browse(cr, uid, node2_id).risk, 0.5)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 8.5)
        # 1-((1-0.307179676972449)*(1-0.452277442494834)*(1-.5))**(1/3.) = 0.4253760143455
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.4253760143455)

        # Move the ticket1 to the new node
        self.tickets.write(cr, self.manager_id, ticket1_id, {'parent_id': node2_id})
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).rating, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).risk, 0.307179676972449)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).rating, 5.5)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).risk, 0.452277442494834)
        self.assertEquals(self.tickets.browse(cr, uid, node_id).rating, 5.5)
        self.assertEquals(self.tickets.browse(cr, uid, node_id).risk, 0.452277442494834)
        self.assertEquals(self.tickets.browse(cr, uid, node2_id).rating, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, node2_id).risk, 0.307179676972449)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.383985942351795)

        # We also move the ticket2, and the node1 is now empty
        self.tickets.write(cr, self.manager_id, ticket2_id, {'parent_id': node2_id})
        self.assertEquals(self.tickets.browse(cr, uid, node_id).rating, 0.0)
        self.assertEquals(self.tickets.browse(cr, uid, node_id).risk, 0.5)
        self.assertEquals(self.tickets.browse(cr, uid, node2_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, node2_id).risk, 0.383985942351795)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.4253760143455)
        # we remove the 1st node,
        self.tickets.unlink(cr, uid, [node_id])
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.383985942351795)

        # Now create a second project and move the tickets
        project2_id = self.tickets.create(
            cr, self.manager_id,
            {'name': 'Project2',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test2')})
        node3_id = self.tickets.create(cr, self.manager_id,
                                       {'name': 'Node3', 'parent_id': project2_id, })

        # move the ticket1 to the node3
        self.tickets.write(cr, self.manager_id, ticket1_id, {'parent_id': node3_id})
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).rating, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).risk, 0.307179676972449)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).rating, 5.5)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).risk, 0.452277442494834)
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).rating, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).risk, 0.307179676972449)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).rating, 5.5)
        self.assertEquals(self.tickets.browse(cr, uid, project_id).risk, 0.452277442494834)
        self.assertEquals(self.tickets.browse(cr, uid, project2_id).rating, 3.0)
        self.assertEquals(self.tickets.browse(cr, uid, project2_id).risk, 0.307179676972449)

        # We also move the ticket2, and the node2 is now empty
        self.tickets.write(cr, self.manager_id, ticket2_id, {'parent_id': node3_id})
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).risk, 0.383985942351795)
        self.assertEquals(self.tickets.browse(cr, uid, project2_id).rating, 8.5)
        self.assertEquals(self.tickets.browse(cr, uid, project2_id).risk, 0.383985942351795)

        # we delete the project1 and node2
        self.tickets.unlink(cr, uid, [project_id, node2_id])
        # Moved tickets are in the correct project
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).project_id.id, project2_id)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).project_id.id, project2_id)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).method_id.name, 'Test2')

        # Recreated the project1 and move the whole node3 at once
        project_id = self.tickets.create(
            cr, self.manager_id,
            {'name': 'Project1',
             'participant_ids': [(6, 0, [self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})

        self.tickets.write(cr, self.manager_id, node3_id, {'parent_id': project_id})
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).project_id.id, project_id)
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).project_id.id, project_id)
        self.assertEquals(self.tickets.browse(cr, uid, ticket2_id).project_id.id, project_id)
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).method_id.name, 'Test')
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).method_id.name, 'Test')

        # we change the method of the project1
        self.tickets.write(cr, uid, project_id, {'method_id': self.ref('anytracker.method_test2')})
        self.assertEquals(self.tickets.browse(cr, uid, node3_id).method_id.name, 'Test2')
        self.assertEquals(self.tickets.browse(cr, uid, ticket1_id).method_id.name, 'Test2')
