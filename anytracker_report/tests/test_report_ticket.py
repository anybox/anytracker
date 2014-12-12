from .ReportTestCase import ReportTestCase


class TestTickets(ReportTestCase):

    _report_name = 'ticket_webkit'
    _report_base_model = 'anytracker.ticket'

    @classmethod
    def create_project(cls, participant_ids, **kw):
        """Create a project with given participants and some default values.

        :param kw: additional field values, will override the default ones.
        """
        vals = {'name': "Test project",
                'method_id': cls.ref('anytracker.method_scrum'),
                'participant_ids': [(6, 0, participant_ids)]}
        vals.update(kw)
        return cls.ticket.create(cls.cr, cls.uid, vals)

    @classmethod
    def initTestData(cls):
        super(TestTickets, cls).initTestData()
        cr, uid = cls.cr, cls.uid
        ticket = cls.ticket = cls.registry('anytracker.ticket')
        cls.ticket = ticket
        cls.manager_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker Manager",
                          tz="Europe/Paris",
                          login='at.manager',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_manager')])]))
        cls.member_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker member",
                          tz="Europe/Paris",
                          login='at.user',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_member')])]))
        cls.customer_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker customer",
                          tz="Europe/Paris",
                          login='at.cust',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_customer')])]))

        pid = cls.project_id = cls.create_project([cls.manager_id, cls.member_id, cls.customer_id],
                                                  name="Main test project")
        cls.pid = pid
        cls.t1_id = ticket.create(cr, uid, dict(name="First ticket",
                                                description="Ticket description",
                                                parent_id=pid))
        cls.t2_id = ticket.create(cr, uid, dict(name="Second ticket",
                                                description="Ticket description",
                                                parent_id=pid))
        cls.t3_id = ticket.create(cr, uid, dict(name="Third ticket",
                                                description="Ticket description",
                                                parent_id=pid))

        cls.admin_id = cls.uid

    def test_parser_test_methode(self):
        """Example test parse methode"""
        self.assertFalse(self.getParser()._test_methode())

    def test_report(self):
        """Launch one ticket report"""
        self.generateReport([self.t1_id])

    def test_report_multi_ticket(self):
        """Launch report with many tickets"""
        self.generateReport([self.t1_id, self.t2_id, self.t3_id])

    def test_report_without_description(self):
        ticket_id_without_desc = self.ticket.create(
            self.cr, self.uid, dict(name="Third ticket", parent_id=self.pid))
        self.generateReport([self.t1_id, ticket_id_without_desc, self.t3_id])

    def test_report_ticket_by_customer(self):
        self.generateReport([self.t1_id, self.t2_id, self.t3_id], user_id=self.customer_id)

    def test_report_ticket_by_member(self):
        self.generateReport([self.t1_id, self.t2_id, self.t3_id], user_id=self.member_id)

    def test_report_ticket_by_manager(self):
        self.generateReport([self.t1_id, self.t2_id, self.t3_id], user_id=self.manager_id)
