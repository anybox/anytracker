from os.path import join

from anybox.testing.openerp import SharedSetupTransactionCase
from odoo.osv import orm


class TestImportance(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestImportance, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        USER = cls.env['res.users']
        cls.IMPORTANCE = cls.env['anytracker.importance']

        cls.importance_must = cls.ref('anytracker.test_imp_musthave')
        cls.importance_should = cls.ref('anytracker.test_imp_shouldhave')
        cls.importance_nice = cls.ref('anytracker.test_imp_nicetohave')
        cls.customer_id = USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_customer')])]}
        ).id

    def test_importance(self):
        # create a project and a ticket
        project = self.TICKET.create({
            'name': 'test project',
            'participant_ids': [(6, 0, [self.customer_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.TICKET.create({
            'name': 'Test simple ticket',
            'parent_id': project.id})
        # we check that a default importance has been set
        self.assertEquals(ticket.importance_id.name, 'SHOULD HAVE')
        # the customer sets another importance
        ticket.sudo(self.customer_id).write(
            {'importance_id': self.importance_must})
        self.assertEquals(ticket.importance_id.seq, 30)
        self.assertEquals(ticket.importance, 30)
        self.assertEquals(ticket.importance_id.name, 'MUST HAVE')
        ticket.sudo(self.customer_id).write(
            {'importance_id': self.importance_should})
        self.assertEquals(ticket.importance_id.seq, 20)
        self.assertEquals(ticket.importance, 20)
        # we no default importance we have nothing on the ticket
        self.IMPORTANCE.browse(self.importance_should).write(
            {'default': False})
        ticket = self.TICKET.create({
            'name': 'Test simple ticket with no default priorities',
            'parent_id': project.id})
        self.assertEquals(ticket.importance_id.id, False)
        self.assertEquals(ticket.importance, False)
        # with two default importances we get a config error
        self.IMPORTANCE.browse(self.importance_nice).write({'default': True})
        self.IMPORTANCE.browse(self.importance_should).write({'default': True})
        self.assertRaises(
            orm.except_orm,
            self.TICKET.create,
            {'name': 'Test simple ticket with 2 default priorities',
             'parent_id': project.id})
        # check order
        self.IMPORTANCE.browse(self.importance_should).write(
            {'default': False})
        self.IMPORTANCE.browse(self.importance_nice).write(
            {'default': True, 'seq': -1})
        ticket = self.TICKET.create({
            'name': 'Test simple ticket with negative priority',
            'parent_id': project.id})
        tickets = self.TICKET.search([
            ('method_id', '=', self.ref('anytracker.method_test')),
            ('type', '=', 'ticket')])
        self.assertEquals([t.importance for t in tickets], [20, 0, -1])
        # in case we change the seq of an importance,
        # the stored field should change as well
        self.IMPORTANCE.browse(self.importance_nice).write({'seq': -2})
        self.assertEquals(ticket.importance, -2)
