from openerp import netsvc
from anybox.testing.openerp import SharedSetupTransactionCase


class TestBouquets(SharedSetupTransactionCase):

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

        cls.reportService = netsvc.LocalService('report.bouquet_webkit')
        cls._bouquet_parser = cls.reportService.parser(
            cr, uid, cls.reportService.name, context=None)

        ticket = cls.ticket = cls.registry('anytracker.ticket')
        cls.bouquet = cls.registry('anytracker.bouquet')

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
        t1_id = ticket.create(cr, uid, dict(name="First ticket", parent_id=pid))
        t2_id = ticket.create(cr, uid, dict(name="Second ticket", parent_id=pid))
        cls.ticket_ids = [t1_id, t2_id]
        cls.bouquet_id = cls.create_bouquet(name=u"Un bouquet ?", ticket_ids=cls.ticket_ids)

        t3_id = ticket.create(cr, uid, dict(name="Third ticket", parent_id=pid))
        cls.bouquet2_id = cls.create_bouquet(name=u"Un bouquet ?", ticket_ids=[t1_id, t3_id])

        cls.admin_id = cls.uid

    def test_parser_test_methode(self):
        """test parse methode"""
        self.assertTrue(self._bouquet_parser._test_methode())

    def test_report(self):
        """launch bouquet report"""
        cr, uid = self.cr, self.uid
        (result, format) = self.reportService.create(cr, uid, [self.bouquet_id],
                                                     {'model': 'anytracker.bouquet'}, context=None)
        (result, format) = self.reportService.create(cr, uid, [self.bouquet_id, self.bouquet2_id],
                                                     {'model': 'anytracker.bouquet'}, context=None)
