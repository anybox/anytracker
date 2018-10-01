# coding: utf-8
from os.path import join
from psycopg2 import IntegrityError
from anybox.testing.openerp import SharedSetupTransactionCase
from odoo.exceptions import AccessError


class TestTag(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestTag, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.TAG = cls.env['anytracker.tag']
        cls.my_tag = cls.TAG.create({'name': "My tag"})
        USER = cls.env['res.users']
        cls.member = USER.create({
            'name': 'test member',
            'login': 'test',
            'email': 'member@localhost',
            'groups_id': [(6, 0,
                           [cls.ref('base.group_user'), cls.ref('anytracker.group_member')])]}
        )
        cls.customer = USER.create(
            {'name': 'test customer stage',
             'login': 'test_customer_stage',
             'email': 'test_customer@localhost',
             'groups_id': [(6, 0, [
                 # FIXME: base.group_user actually needed exclusively during u test
                 # for 'mail.activity.mixin' fields with groups='base.group_user'
                 # during ticket write
                 # (in real case ticket is writable without base.group_user)
                 cls.ref('base.group_user'),
                 cls.ref('anytracker.group_customer')])]
             }
        )

    def test_tag_access(self):
        project = self.TICKET.create({
            'name': 'Test',
            'tags': [(6, 0, [self.my_tag.id])],
            'participant_ids': [(6, 0, [self.member.id, self.customer.id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.TICKET.sudo(self.member).create({
            'name': 'Ticket to move',
            'tags': [(6, 0, [self.my_tag.id])],
            'parent_id': project.id, })
        with self.assertRaises(AccessError):
            ticket.sudo(self.customer).tags[0].name = "test"

    def test_tag_uniq(self):
        self.TAG.create({'name': "tag 1"})
        with self.assertRaises(IntegrityError):
            self.TAG.create({'name': "tag 1"})
