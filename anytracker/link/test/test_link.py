# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import orm
from openerp.exceptions import AccessError
from os.path import join


class TestLink(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestLink, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TYPELINK = cls.env['anytracker.link.type']
        cls.LINK = cls.env['anytracker.link']

        cls.TICKET = cls.env['anytracker.ticket']
        USER = cls.env['res.users']

        """
        We have 3 persons: 1 member, 1 partner, 1 custommer
        """
        cls.member_id = USER.create({
            'name': 'test member',
            'login': 'test',
            'email': 'member@localhost',
            'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member')])]}
        ).id
        cls.customer_id = USER.create(
            {'name': 'test customer stage',
             'login': 'test_customer_stage',
             'groups_id': [(6, 0, [cls.ref('anytracker.group_customer')])]}
        ).id
        cls.partner_id = USER.create(
            {'name': 'test partner stage',
             'login': 'test_partner_stage',
             'groups_id': [(6, 0, [cls.ref('anytracker.group_partner')])]}
        ).id
        """
            We have 3 projects: 
               a user case project: with member, partner, customer access
               a technical project: with member, partner access
               a ultra technical project: with member only access        
        """
        cls.projet_us = cls.TICKET.create({
            'name': 'Test us',
            'participant_ids': [(6, 0, [cls.member_id, cls.customer_id, cls.partner_id])],
            'method_id': cls.ref('anytracker.method_test')})

        cls.projet_technical = cls.TICKET.create({
            'name': 'Test technical',
            'participant_ids': [(6, 0, [cls.member_id, cls.partner_id])],
            'method_id': cls.ref('anytracker.method_test')})

        cls.projet_ultra_technical = cls.TICKET.create({
            'name': 'Test ultra technical',
            'participant_ids': [(6, 0, [cls.member_id])],
            'method_id': cls.ref('anytracker.method_test')})

        """
            We create 2 tickets for each project
        
        """
        cls.ticket_us_1 = cls.TICKET.create({
            'name': 'Test us 1',
            'parent_id': cls.projet_us.id, })

        cls.env['res.partner'].sudo().create({'name': "A Partner"})

        cls.ticket_us_2 = cls.TICKET.create({
            'name': 'Test us 2',
            'parent_id': cls.projet_us.id, })

        cls.ticket_tech_1 = cls.TICKET.create({
            'name': 'Test tech 1',
            'parent_id': cls.projet_technical.id, })


        cls.ticket_tech_2= cls.TICKET.create({
            'name': 'Test tech 2',
            'parent_id': cls.projet_technical.id, })

        cls.ticket_ultra_tech_1 = cls.TICKET.create({
            'name': 'Test ultra tech 1',
            'parent_id': cls.projet_ultra_technical.id, })


        cls.ticket_ultra_tech_2= cls.TICKET.create({
            'name': 'Test ultra tech 2',
            'parent_id': cls.projet_ultra_technical.id, })

        cls.link_type1 = cls.TYPELINK.sudo().create({
            'name': 'type1',
            'description': 'type_description',
        })
    """
     TEST FOR TYPE_LINK
    """

    def test_create_type_link_admin(self):
       """Admin can create Type Link"""
       link_type1 = self.TYPELINK.sudo().create({
           'name': 'type1',
           'description': 'type_description',
       })

       # Search by link type name
       link_type_by_name = self.TYPELINK.search([
           ('name', '=', link_type1.name)])

       # Check result
       for i in range(len(link_type_by_name)):
           self.assertEquals(link_type_by_name[i].name, link_type1.name)

    def test_create_type_link_by_member(self):
        """Member not authorized to create type link"""
        with self.assertRaises(AccessError):
           self.TYPELINK.sudo(self.member_id).create({
            'name': 'type1',
            'description': 'type_description',
           })

    def test_create_type_link_by_partner(self):
        """Partner not authorized to create type link"""
        with self.assertRaises(AccessError):
           self.TYPELINK.sudo(self.partner_id).create({
            'name': 'type1',
            'description': 'type_description',
           })

    def test_create_type_link_by_customer(self):
       """Customer not authorized to create type link"""
       with self.assertRaises(AccessError):
           self.TYPELINK.sudo(self.customer_id).create({
               'name': 'type1',
               'description': 'type_description',
           })

    """
     TEST FOR LINK
    """
    def test_create_link_by_member(self):
       """Member can create Link"""
       link_1 = self.LINK.sudo(self.member_id).create({
           'ticket_one': self.ticket_us_1.id,
           'ticket_two': self.ticket_tech_2.id,
           'linktype_id': self.link_type1.id,
       })

       # Search by link id
       link_by_id= self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.member_id).search([
           ('id', '=', link_1.id)])

       # Check result
       for i in range(len(link_by_id)):
           self.assertEquals(link_by_id[i].name, self.ticket_tech_2.name)

    def test_create_link_by_partner(self):
       """Partner can create  Link"""
       link_1 = self.LINK.sudo(self.partner_id).create({
           'ticket_one': self.ticket_us_1.id,
           'ticket_two': self.ticket_tech_2.id,
           'linktype_id': self.link_type1.id,
       })

       # Search by link id
       link_by_id= self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.member_id).search([
           ('id', '=', link_1.id)])

       # Check result
       for i in range(len(link_by_id)):
           self.assertEquals(link_by_id[i].name, self.ticket_tech_2.name)

    def test_create_link_customer(self):
       """Customer can not create link"""
       with self.assertRaises(AccessError):
           self.LINK.sudo(self.customer_id).create({
               'ticket_one': self.ticket_us_1.id,
               'ticket_two': self.ticket_us_2.id,
               'linktype_id': self.link_type1.id,
           })

    def test_read_authorized_link_partner(self):
       """Partner can read authorized link """
       link_1 = self.LINK.sudo().create({
           'ticket_one': self.ticket_us_1.id,
           'ticket_two': self.ticket_tech_2.id,
           'linktype_id': self.link_type1.id,
       })

       # Search by link id
       link_by_id = self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.partner_id).search([
           ('id', '=', link_1.id)])

       # Check result
       for i in range(len(link_by_id)):
           self.assertEquals(link_by_id[i].name, self.ticket_tech_2.name)

    def test_read_unauthorized_link_partner(self):
       """Partner can not read unauthorized link """
       link_1 = self.LINK.sudo().create({
           'ticket_one': self.ticket_us_1.id,
           'ticket_two': self.ticket_ultra_tech_2.id,
           'linktype_id': self.link_type1.id,
       })

       # Search by link type name
       link_by_id = self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.partner_id).search([
           ('id', '=', link_1.id)])

       # Check result
       for i in range(len(link_by_id)):
           with self.assertRaises(AccessError):
             link_by_id[i].name


    def test_read_authorized_link_custommer(self):
       """Customer can read authorized link """
       link_1 = self.LINK.sudo().create({
           'ticket_one': self.ticket_us_1.id,
           'ticket_two': self.ticket_us_2.id,
           'linktype_id': self.link_type1.id,
       })

       # Search by link id
       link_by_id = self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.customer_id).search([
           ('id', '=', link_1.id)])

       # Check result
       for i in range(len(link_by_id)):
           self.assertEquals(link_by_id[i].name, self.ticket_us_2.name)

    def test_read_unauthorized_link_customer(self):
       """Customer can not read unauthorized link """
       link_1 = self.LINK.sudo().create({
           'ticket_one': self.ticket_us_1.id,
           'ticket_two': self.ticket_tech_2.id,
           'linktype_id': self.link_type1.id,
       })

       # Search by link type name
       link_by_id = self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.customer_id).search([
           ('id', '=', link_1.id)])

       # Check result
       for i in range(len(link_by_id)):
           with self.assertRaises(AccessError):
             link_by_id[i].name

    def test_remove_link_member(self):
        """Member can remove link"""
        link_1 = self.LINK.sudo(self.member_id).create({
            'ticket_one': self.ticket_us_1.id,
            'ticket_two': self.ticket_tech_2.id,
            'linktype_id': self.link_type1.id,
        })

        link_1.sudo(self.member_id).unlink()

        # Search by link type name
        link_by_id = self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.member_id).search([
            ('id', '=', link_1.id)])

        self.assertEquals(len(link_by_id), 0)

    def test_remove_link_partner(self):
         """Partner can remove link"""
         link_1 = self.LINK.sudo(self.member_id).create({
             'ticket_one': self.ticket_us_1.id,
             'ticket_two': self.ticket_tech_2.id,
             'linktype_id': self.link_type1.id,
         })

         link_1.sudo(self.partner_id).unlink()

         # Search by link type name
         link_by_id = self.LINK.with_context(active_id=self.ticket_us_1).sudo(self.partner_id).search([
             ('id', '=', link_1.id)])

         self.assertEquals(len(link_by_id), 0)

    def test_remove_link_customer(self):
         """Customer can not remove link"""
         link_1 = self.LINK.sudo(self.member_id).create({
             'ticket_one': self.ticket_us_1.id,
             'ticket_two': self.ticket_us_2.id,
             'linktype_id': self.link_type1.id,
         })

         with self.assertRaises(AccessError):
             link_1.sudo(self.customer_id).unlink()




