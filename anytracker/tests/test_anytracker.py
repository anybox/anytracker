from anybox.testing.openerp import SharedSetupTransactionCase
from odoo.exceptions import except_orm
import base64


class TestAnytracker(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = ('data.xml',)

    @classmethod
    def initTestData(cls):
        super(TestAnytracker, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.ATTACHMENT = cls.env['ir.attachment']
        cls.USER = cls.env['res.users']
        cls.PARTNER = cls.env['res.partner']

        cls.member_id = cls.USER.create(
            {'name': 'Member',
             'login': 'member',
             'email': 'member@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]}
        ).id
        cls.manager_id = cls.USER.create(
            {'name': 'Manager',
             'login': 'manager',
             'email': 'manager@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('base.group_user'),
                            cls.ref('anytracker.group_manager')])]}
        ).id
        cls.customer_id = cls.USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'email': 'customer@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_customer')])]}
        ).id

    def test_name_search_and_autosubscribe(self):
        """
            Test the name_search function in anytracker.ticket module.
            We may be able to find a ticket from his name or number.
            Also test that project members are subscribed to the openchatter
        """
        # Create a project and a ticket
        project = self.TICKET.create(
            {'name': 'Test1',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})
        # check project_id attribute exists
        self.assertEquals(project.project_id.id, project.id)

        ticket = self.TICKET.create(
            {'name': 'Test simple ticket', 'parent_id': project.id})

        # we check there are 4 subscribers (uid/admin + the 3 project members)
        self.assertEquals(len(ticket.message_follower_ids), 4)

        # Search by name
        ticket_id_by_name = self.TICKET.search([
            ('name', '=', 'Test simple ticket')])

        # Search by ticket number
        ticket_id_by_number = self.TICKET.search([
            ('name', '=', ticket.number)])

        # Check result
        for i in range(len(ticket_id_by_name)):
            self.assertEquals(ticket_id_by_name[i], ticket)

        for j in range(len(ticket_id_by_number)):
            self.assertEquals(ticket_id_by_number[j], ticket)

    def test_fulltext(self):
        project = self.TICKET.create(
            {'name': 'Foo',
             'description': 'Bar',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})

        self.assertTrue(
            project in self.TICKET.search([('fulltext', 'ilike', 'foo')]))
        self.assertTrue(
            project in self.TICKET.search([('fulltext', 'ilike', 'bar')]))
        number = str(project.number)
        self.assertTrue(
            project in self.TICKET.search([('fulltext', 'ilike', number)]))
        self.assertEqual(
            len(self.TICKET.search([('fulltext', 'ilike', '###nomatch###')])),
            0)

    def test_disable_project(self):
        """ Set a node as inactive, and check all subtickets are also inactive
        """
        # create a project
        project = self.TICKET.create(
            {'name': 'Test2',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})
        # create a sub node and 2 tickets
        node = self.TICKET.create({
            'name': 'A node',
            'parent_id': project.id})
        self.TICKET.create({'name': 'ticket1', 'parent_id': node.id, })
        self.TICKET.create({'name': 'ticket2', 'parent_id': node.id, })
        # check that we can find all the tickets of the project
        self.assertEquals(
            4, self.TICKET.search([
                ('id', 'child_of', project.id)], count=True))
        # set the project as inactive
        project.write({'active': False})
        # check that we CANNOT find all the tickets of the project
        self.assertEquals(
            0, self.TICKET.search([
                ('id', 'child_of', project.id)], count=True))
        # set the project as active again
        project.write({'active': True})
        # check that we can find again all the tickets of the project
        self.assertEquals(
            4, self.TICKET.search([
                ('id', 'child_of', project.id)], count=True))

    def test_attachments(self):
        """ Check attachment creation, deletion and access
        """
        # create a project
        project = self.TICKET.create(
            {'name': 'Attachment test',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_maintenance')})
        # let the customer create a ticket and an attachment
        ticket = self.TICKET.sudo(self.customer_id).create(
            {'name': 'A ticket',
             'parent_id': project.id,
             'my_rating': False}
        )
        # False should be ignored at creation
        attach1 = self.ATTACHMENT.sudo(self.customer_id).create({
            'name': 'testfile',
            'db_datas': base64.b64encode('0000'),
            'datas_fname': 'testfile',
            'res_model': 'anytracker.ticket',
            'res_id': ticket.id,
        })
        # don't let the customer delete his attachment
        self.assertRaises(except_orm, attach1.sudo(self.customer_id).unlink)
        # check the customer cannot access an attachment of another project
        project = self.TICKET.create(
            {'name': 'Attachment test2',
             'participant_ids': [(6, 0, [self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_maintenance')})
        ticket = self.TICKET.sudo(self.member_id).create(
            {'name': 'A ticket2', 'parent_id': project.id, })
        attach2 = self.ATTACHMENT.sudo(self.member_id).create({
            'name': 'testfile2',
            'db_datas': base64.b64encode('1111'),
            'datas_fname': 'testfile2',
            'res_model': 'anytracker.ticket',
            'res_id': ticket.id,
        })
        attach_ids = self.ATTACHMENT.sudo(self.customer_id).search(
            [('id', 'in', (attach1.id, attach2.id))])
        self.assertEquals(attach_ids.ids, [attach1.id])
        self.assertRaises(except_orm,
                          getattr, attach2.sudo(self.customer_id), 'name')

    def test_customer_access(self):
        """ Protect sensitive data
        """
        project = self.TICKET.sudo(self.member_id).create(
            {'name': 'Partner access test',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_maintenance')})
        # create a partner as manager
        partner = self.PARTNER.sudo().create({
            'name': 'test partner', 'email': 'test@example.com'})
        # customer cannot search or access partners,
        # except anytracker user and partner linked to its company
        partner_ids = self.PARTNER.sudo(self.customer_id).search([])
        self.assertEquals(len(partner_ids), 4)
        self.assertRaises(except_orm,
                          partner.sudo(self.customer_id).read, ['name'])
        self.assertRaises(except_orm,
                          partner.sudo(self.customer_id).read, ['email'])

        # users are protected as well
        user_ids = self.PARTNER.sudo(self.customer_id).search([])
        self.assertEquals(len(user_ids), 4)
        # The customer can access the member user
        member = self.USER.browse(self.member_id)
        mb_partner = member.sudo(self.customer_id).partner_id
        self.assertEquals(mb_partner.email, 'member@localhost')
        # But not if the member is no more in the project
        project.write({'participant_ids': [(3, self.member_id)]})
        # (cache should be cleared)
        self.assertRaises(except_orm, getattr, mb_partner, 'email')
        self.assertRaises(except_orm, mb_partner.read, ['email'])
        # The customer can read but not write the partner linked to its company
        customer = self.USER.sudo(self.customer_id).browse(self.customer_id)
        self.assertEquals('@' in customer.company_id.partner_id.email, True)
        self.assertRaises(except_orm, customer.company_id.partner_id.write,
                          {'email': 'test@test.fr'})

    def test_move_tickets(self):
        """ Check that we can move a ticket to another node or project
        and that everything is still consistent
        """
        # create a first project with 3 tickets
        project = self.TICKET.sudo(self.manager_id).create(
            {'name': 'Project1',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})
        self.assertEquals(project.rating, 0.0)
        self.assertEquals(project.risk, 0.5)

        node = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Node1', 'parent_id': project.id, })
        self.assertEquals(node.rating, 0.0)
        self.assertEquals(node.risk, 0.5)
        ticket1 = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Ticket1', 'parent_id': node.id, })
        ticket2 = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Ticket2', 'parent_id': node.id, })

        # rate the tickets and set the stage
        ticket1.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity1')})
        # I change my mind and set another complexity
        ticket1.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity2'),
            'stage_id': self.ref('anytracker.stage_test_todo')})
        ticket2.sudo(self.member_id).write({
            'my_rating': self.ref('anytracker.complexity4'),
            'stage_id': self.ref('anytracker.stage_test_doing')})
        # the manager also rates the tickets
        ticket1.sudo(self.manager_id).write(
            {'my_rating': self.ref('anytracker.complexity3')})
        ticket2.sudo(self.manager_id).write(
            {'my_rating': self.ref('anytracker.complexity3')})

        # check the progress and risk
        self.assertEquals(ticket1.rating, 3.0)
        self.assertEquals(ticket1.risk, 0.307179676972449)
        self.assertEquals(ticket2.rating, 5.5)
        self.assertEquals(ticket2.risk, 0.452277442494834)
        self.assertEquals(project.rating, 8.5)
        # 1-((1-0.30717967697)*(1-0.45227744249))**(1/2.) = 0.38398594235
        self.assertEquals(project.risk, 0.383985942351795)
        self.assertEquals(node.rating, 8.5)
        self.assertEquals(node.risk, 0.383985942351795)

        # Now create a second empty node
        node2 = self.TICKET.sudo(self.member_id).create(
            {'name': 'Node2', 'parent_id': project.id})
        self.assertEquals(node2.rating, 0.0)
        self.assertEquals(node2.risk, 0.5)
        self.assertEquals(project.rating, 8.5)
        # 1-((1-0.30717967697)*(1-0.45227744249)*(1-.5))**(1/3.) = 0.425376014
        self.assertEquals(project.risk, 0.4253760143455)

        # Move the ticket1 to the new node
        ticket1.sudo(self.manager_id).write({'parent_id': node2.id})
        self.assertEquals(ticket1.rating, 3.0)
        self.assertEquals(ticket1.risk, 0.307179676972449)
        self.assertEquals(ticket2.rating, 5.5)
        self.assertEquals(ticket2.risk, 0.452277442494834)
        self.assertEquals(node.rating, 5.5)
        self.assertEquals(node.risk, 0.452277442494834)
        self.assertEquals(node2.rating, 3.0)
        self.assertEquals(node2.risk, 0.307179676972449)
        self.assertEquals(project.rating, 8.5)
        self.assertEquals(project.risk, 0.383985942351795)

        # We also move the ticket2, and the node1 is now empty
        ticket2.sudo(self.manager_id).write({'parent_id': node2.id})
        self.assertEquals(node.rating, 0.0)
        self.assertEquals(node.risk, 0.5)
        self.assertEquals(node2.rating, 8.5)
        self.assertEquals(node2.risk, 0.383985942351795)
        self.assertEquals(project.rating, 8.5)
        self.assertEquals(project.risk, 0.383985942351795)
        # we remove the 1st node,
        node.sudo(self.manager_id).unlink()
        self.assertEquals(project.rating, 8.5)
        self.assertEquals(project.risk, 0.383985942351795)

        # Now create a second project and move the tickets
        project2 = self.TICKET.sudo(self.manager_id).create(
            {'name': 'Project2',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test2')})
        node3 = self.TICKET.sudo(self.manager_id).create(
            {'name': 'Node3', 'parent_id': project2.id, })

        # move the ticket1 to the node3
        ticket1.sudo(self.manager_id).write({'parent_id': node3.id})
        self.assertEquals(ticket1.rating, 3.0)
        self.assertEquals(ticket1.risk, 0.307179676972449)
        self.assertEquals(ticket2.rating, 5.5)
        self.assertEquals(ticket2.risk, 0.452277442494834)
        self.assertEquals(node3.rating, 3.0)
        self.assertEquals(node3.risk, 0.307179676972449)
        self.assertEquals(project.rating, 5.5)
        self.assertEquals(project.risk, 0.452277442494834)
        self.assertEquals(project2.rating, 3.0)
        self.assertEquals(project2.risk, 0.307179676972449)

        # We also move the ticket2, and the node2 is now empty
        ticket2.sudo(self.manager_id).write({'parent_id': node3.id})
        self.assertEquals(node3.rating, 8.5)
        self.assertEquals(node3.risk, 0.383985942351795)
        self.assertEquals(project2.rating, 8.5)
        self.assertEquals(project2.risk, 0.383985942351795)

        # we delete the project1 and node2
        node2.unlink()
        project.unlink()
        # Moved tickets are in the correct project
        self.assertEquals(ticket1.project_id.id, project2.id)
        self.assertEquals(ticket2.project_id.id, project2.id)
        self.assertEquals(ticket1.method_id.name, 'Test2')

        # Recreated the project1 and move the whole node3 at once
        project1 = self.TICKET.create(
            {'name': 'Project1',
             'participant_ids': [(6, 0, [
                 self.customer_id, self.member_id, self.manager_id])],
             'method_id': self.ref('anytracker.method_test')})

        node3.sudo(self.manager_id).write({'parent_id': project1.id})
        self.assertEquals(node3.project_id.id, project1.id)
        self.assertEquals(ticket1.project_id.id, project1.id)
        self.assertEquals(ticket2.project_id.id, project1.id)
        self.assertEquals(node3.method_id.name, 'Test')
        self.assertEquals(ticket1.method_id.name, 'Test')

        # we change the method of the project1
        project1.write({'method_id': self.ref('anytracker.method_test2')})
        self.assertEquals(node3.method_id.name, 'Test2')
        self.assertEquals(ticket1.method_id.name, 'Test2')

        # we trash the ticket1
        self.assertEquals(project1.risk, 0.5)
        self.assertEquals(project1.rating, 0.0)
        self.assertEquals(project1.progress, 1.0)
        # rate the ticket1
        ticket1.sudo(self.member_id).write(
            {'my_rating': self.ref('anytracker.complexity7')})
        self.assertEquals(ticket1.rating, 4.5)
        self.assertEquals(ticket1.risk, 0.45)
        self.assertEquals(ticket1.progress, 5.0)
        self.assertEquals(project1.risk, 0.475595575914924)
        self.assertEquals(project1.rating, 4.5)
        self.assertEquals(project1.progress, 1.0)
        # trash the ticket1,
        # and check the risk, rating and progress of the project is updated
        ticket1.trash()
        self.assertEquals(ticket1.progress, 100.0)
        self.assertEquals(project1.risk, 0.5)
        self.assertEquals(project1.rating, 0.0)
        self.assertEquals(project1.progress, 1.0)

    def test_ticket_type(self):
        """ Tickets have a type """
        # create a first project with 1 subnode and 2 tickets
        project = self.TICKET.sudo(self.manager_id).create(
            {
                'name': 'Project1',
                'participant_ids': [(6, 0, [
                    self.customer_id, self.member_id, self.manager_id
                ])],
                'method_id': self.ref('anytracker.method_test')
            }
        )
        node = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Node1', 'parent_id': project.id, })
        ticket1 = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Ticket1', 'parent_id': node.id, })
        ticket2 = self.TICKET.sudo(self.customer_id).create(
            {'name': 'Ticket2', 'parent_id': node.id, })
        # We have 2 natives types: 'node', 'ticket', automatically assigned
        self.assertEquals(project.type.code, 'node')
        self.assertEquals(node.type.code, 'node')
        self.assertEquals(ticket1.type.code, 'ticket')
        self.assertEquals(ticket2.type.code, 'ticket')

    def test_breadcrumbs(self):
        """Test extraction of ticket paths."""
        # create a project, a node and two tickets in the node
        project = self.TICKET.sudo(self.manager_id).create(
            {'name': 'Proj',
             'method_id': self.ref('anytracker.method_test'),
             'participant_ids':
                [(6, 0, [self.customer_id, self.member_id, self.manager_id])]})

        node1 = self.TICKET.sudo(self.customer_id).create({
            'name': "Node1",
            'parent_id': project.id})
        t11 = self.TICKET.sudo(self.customer_id).create({
            'name': "Ticket11",
            'parent_id': node1.id})
        t12 = self.TICKET.sudo(self.customer_id).create({
            'name': "Ticket12",
            'parent_id': node1.id})

        self.assertEqual(
            (t11 + t12).sudo(self.customer_id).get_breadcrumb(),
            {t11.id: [dict(id=project.id, parent_id=None, name="Proj"),
                      dict(id=node1.id, parent_id=project.id, name="Node1"),
                      dict(id=t11.id, parent_id=node1.id, name="Ticket11"),
                      ],
             t12.id: [dict(id=project.id, parent_id=None, name="Proj"),
                      dict(id=node1.id, parent_id=project.id, name="Node1"),
                      dict(id=t12.id, parent_id=node1.id, name="Ticket12"),
                      ],
             })

        # Now relative breadcrumbs
        self.assertEqual(
            (t11 + t12).sudo(self.customer_id
                             ).get_breadcrumb(under_node_id=project.id),
            {t11.id: [dict(id=node1.id, parent_id=project.id, name="Node1"),
                      dict(id=t11.id, parent_id=node1.id, name="Ticket11"),
                      ],
             t12.id: [dict(id=node1.id, parent_id=project.id, name="Node1"),
                      dict(id=t12.id, parent_id=node1.id, name="Ticket12"),
                      ],
             })
        self.assertEqual(
            (t11 + t12).sudo(self.customer_id
                             ).get_breadcrumb(under_node_id=node1.id),
            {t11.id: [dict(id=t11.id, parent_id=node1.id, name="Ticket11")],
             t12.id: [dict(id=t12.id, parent_id=node1.id, name="Ticket12")],
             })

        # Adding a node to test with branches of different lengths
        n13 = self.TICKET.sudo(self.customer_id).create({
            'name': "Node13",
            'parent_id': node1.id})
        t131 = self.TICKET.sudo(self.customer_id).create({
            'name': "Ticket131",
            'parent_id': n13.id})
        self.assertEqual(
            (t11 + t131).sudo(self.customer_id
                              ).get_breadcrumb(under_node_id=node1.id),
            {t11.id: [dict(id=t11.id, parent_id=node1.id, name="Ticket11")],
             t131.id: [dict(id=n13.id, parent_id=node1.id, name="Node13"),
                       dict(id=t131.id, parent_id=n13.id, name="Ticket131"),
                       ],
             })
