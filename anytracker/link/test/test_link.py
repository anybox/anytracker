# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.osv import orm
from os.path import join


class TestLink(SharedSetupTransactionCase):

#TODO: En mode custommer ajouter un lien
#TODO: En mode custommer si j'accede à un ticket ayant des liens vers un projet dont je ne suis pas membre lever une
# exeption
#TODO: En mode partner ajouter un lien
#TODO: En mode member ajouter un lien
#TODO: En mode custommer supprimer un lien
#TODO: En mode partner supprimer un lien
#TODO: En mode member supprimer un lien


    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestLink, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TYPELINK = cls.env['anytracker.type.link']
        cls.LINK = cls.env['anytracker.link']
        TICKET = cls.env['anytracker.ticket']
        USER = cls.env['res.users']
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

        cls.projet_custommer = cls.TICKET.create({
            'name': 'Test Custommer',
            'participant_ids': [(6, 0, [cls.member_id, cls.customer_id])],
            'method_id': cls.ref('anytracker.method_test')})

        cls.projet_member = cls.TICKET.create({
            'name': 'Test Member',
            'participant_ids': [(6, 0, [cls.member_id])],
            'method_id': cls.ref('anytracker.method_test')})

        cls.projet_custommer_1 = cls.TICKET.create({
            'name': 'Test Custommer 1',
            'parent_id': cls.projet_custommer, })

        cls.projet_custommer_2 = cls.TICKET.create({
            'name': 'Test Custommer 2',
            'parent_id': cls.projet_custommer, })

        cls.projet_member_1 = cls.TICKET.create({
            'name': 'Test Member 1',
            'parent_id': cls.projet_member, })


        cls.projet_member_2 = cls.TICKET.create({
            'name': 'Test Member 2',
            'parent_id': cls.projet_member, })

    def test_create_type_link(self):
        """ Create Link """
        link_custommer1 = self.TYPELINK.create({
            'name': 'type1',
            'description': 'type_description',
            'state': 'actif' })

        # Search by link type name
        link_type_by_name = self.TYPELINK.search([
            ('name', '=', link_custommer1.name)])

        # Check result
        for i in range(len(link_type_by_name)):
            self.assertEquals(link_type_by_name[i], link_custommer1)
