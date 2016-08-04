from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join


class TestImportance(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestImportance, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        USER = cls.env['res.users']
        cls.RATING = cls.env['anytracker.rating']

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
        """ Simple rating scenario: a manager or member or partner can rate,
        not a customer.
        """
        # create a project with a team of 4 people, and a ticket
        project = self.TICKET.create({
            'name': 'test project',
            'participant_ids': [(6, 0, [self.customer_id])],
            'method_id': self.ref('anytracker.method_test')})
        ticket = self.TICKET.create({
            'name': 'Test simple ticket',
            'parent_id': project.id})
        # the customer sets an importance
        ticket.sudo(self.customer_id).write(
            {'importance_id': self.importance_must})
        self.assertEquals(ticket.importance_id.seq, 30)
        self.assertEquals(ticket.importance, 30)
        ticket.sudo(self.customer_id).write(
            {'importance_id': self.importance_nice})
        self.assertEquals(ticket.importance_id.seq, 10)
        self.assertEquals(ticket.importance, 10)
