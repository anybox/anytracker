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

        cls.member_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker member",
                          login='at.user',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_member')])]))
        cls.customer_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker customer",
                          login='at.cust',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_customer')])]))

        pid = cls.project_id = cls.create_project([cls.member_id, cls.customer_id],
                                                  name="Main test project")
        cls.t1_id = ticket.create(cr, uid, dict(name="First ticket", parent_id=pid))
        cls.t2_id = ticket.create(cr, uid, dict(name="Second ticket", parent_id=pid))
        cls.t3_id = ticket.create(cr, uid, dict(name="Third ticket", parent_id=pid))

        cls.admin_id = cls.uid

    def test_parser_test_methode(self):
        """Example test parse methode"""
        self.assertFalse(self.getParser()._test_methode())

    def test_report(self):
        """Launch one ticket report"""
        self.generateReport([self.t1_id])

    def test_report_multi_ticket(self):
        """Launch report with many tickets"""
        (result, format) = self.generateReport([self.t1_id, self.t2_id, self.t3_id])
