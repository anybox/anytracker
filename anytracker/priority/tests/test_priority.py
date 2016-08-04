from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join


class TestPriority(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestPriority, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        USER = cls.env['res.users']
        cls.RATING = cls.env['anytracker.rating']

        cls.prio_urgent = cls.ref('anytracker.test_prio_urgent')
        cls.prio_prio = cls.ref('anytracker.test_prio_prio')
        cls.prio_normal = cls.ref('anytracker.test_prio_normal')
        cls.customer_id = USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_customer')])]}
        ).id

    def test_priority(self):
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
        # the customer sets a priority
        ticket.sudo(self.customer_id).write({'priority_id': self.prio_urgent})
        self.assertEquals(ticket.priority_id.seq, 10)
        self.assertEquals(ticket.priority, 10)
        ticket.sudo(self.customer_id).write({'priority_id': self.prio_prio})
        self.assertEquals(ticket.priority_id.seq, 20)
        self.assertEquals(ticket.priority, 20)
