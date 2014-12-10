from .ReportTestCase import ReportTestCase


class TestBouquets(ReportTestCase):

    _report_name = 'bouquet_webkit'
    _report_base_model = 'anytracker.bouquet'

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
    def create_bouquet(cls, ticket_ids, **kw):
        """Create a bouquet with given tickets and some default values.

        :param kw: additional field values, will override the default ones.
        """
        vals = {'name': "Test bouquet",
                'ticket_ids': [(6, 0, ticket_ids)]}
        vals.update(kw)
        return cls.bouquet.create(cls.cr, cls.uid, vals)

    @classmethod
    def initTestData(cls):
        super(TestBouquets, cls).initTestData()
        cr, uid = cls.cr, cls.uid
        ticket = cls.ticket = cls.registry('anytracker.ticket')
        cls.bouquet = cls.registry('anytracker.bouquet')

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
        t1_id = ticket.create(cr, uid, dict(name="First ticket", parent_id=pid))
        t2_id = ticket.create(cr, uid, dict(name="Second ticket", parent_id=pid))
        cls.ticket_ids = [t1_id, t2_id]
        cls.bouquet_id = cls.create_bouquet(name=u"Un bouquet ?", ticket_ids=cls.ticket_ids)

        t3_id = ticket.create(cr, uid, dict(name="Third ticket", parent_id=pid))
        cls.bouquet2_id = cls.create_bouquet(name=u"Un bouquet ?", ticket_ids=[t1_id, t3_id])

        cls.admin_id = cls.uid

    def test_parser_test_methode(self):
        """Example test parse methode"""
        self.assertTrue(self.getParser()._test_methode())

    def test_report(self):
        """Launch one bouquet report"""
        self.generateReport([self.bouquet_id])

    def test_report_multi_bouquet(self):
        """Launch report with two bouquets"""
        self.generateReport([self.bouquet_id, self.bouquet2_id])

    def test_report_bouquet_without_description(self):
        ticket_id = self.ticket.create(self.cr, self.uid, dict(name="Second ticket",
                                                               description="Ticket description",
                                                               parent_id=self.pid))
        bouquet_id = self.create_bouquet(name=u"Un bouquet ?", ticket_ids=[ticket_id])
        self.generateReport([bouquet_id, self.bouquet2_id])

    def test_report_bouquet_without_ticket(self):
        bouquet_id = self.create_bouquet(name=u"Un bouquet ?",
                                         ticket_ids=[],
                                         description="Bouquet without tickets")
        self.generateReport([bouquet_id, self.bouquet2_id])

    def test_report_bouquet_with_ticket_without_description(self):
        ticket_id = self.ticket.create(self.cr, self.uid, dict(name="Second ticket",
                                                               parent_id=self.pid))
        bouquet_id = self.create_bouquet(name=u"Un bouquet ?", ticket_ids=[ticket_id])
        self.generateReport([bouquet_id, self.bouquet2_id])

    def test_report_bouquet_by_customer(self):
        self.generateReport([self.bouquet_id], user_id=self.customer_id)

    def test_report_bouquet_by_member(self):
        self.generateReport([self.bouquet_id], user_id=self.member_id)

    def test_report_bouquet_by_manager(self):
        self.generateReport([self.bouquet_id], user_id=self.manager_id)
