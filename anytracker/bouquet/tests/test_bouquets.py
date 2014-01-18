from anybox.testing.openerp import SharedSetupTransactionCase


class TestBouquets(SharedSetupTransactionCase):

    @classmethod
    def initTestData(cls):
        super(TestBouquets, cls).initTestData()

        cr, uid = cls.cr, cls.uid
        ticket = cls.ticket = cls.registry('anytracker.ticket')
        cls.bouquet = cls.registry('anytracker.bouquet')

        cls.at_member_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker member",
                          login='at.user',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_member')])]))
        cls.at_cust_id = cls.registry('res.users').create(
            cr, uid, dict(name="anytracker customer",
                          login='at.cust',
                          groups_id=[(6, 0, [cls.ref('anytracker.group_customer')])]))

        pid = cls.project_id = ticket.create(cr, uid,
                                             dict(name="Main test project",
                                                  method_id=cls.ref('anytracker.method_scrum'),
                                                  participant_ids=[(6, 0, [cls.at_member_id,
                                                                           cls.at_cust_id])],
                                                  ))
        t1_id = ticket.create(cr, uid, dict(name="First ticket", parent_id=pid))
        t2_id = ticket.create(cr, uid, dict(name="Second ticket", parent_id=pid))
        cls.ticket_ids = [t1_id, t2_id]

    def test_create_read(self):
        cr, uid, bouquet, tids = self.cr, self.uid, self.bouquet, self.ticket_ids
        bid = bouquet.create(cr, uid, dict(name=u"Un bouquet ?", ticket_ids=[(6, 0, tids)]))
        self.assertRecord(bouquet, bid, dict(ticket_ids=set(tids), nb_tickets=len(tids)),
                          list_to_set=True)

    def test_create_read_perm(self):
        """Create then switch to non-privileged user to check access."""
        cr, bouquet, tids = self.cr, self.bouquet, self.ticket_ids
        bouquet.create(cr, self.uid, dict(name=u"Un bouquet ?", ticket_ids=[(6, 0, tids)]))

        for tested_uid in (self.at_member_id, self.at_cust_id):
            self.uid = tested_uid
            # if this fails, fix the main part of Anytracker first (no other unit tests at this
            # time of writing):
            self.assertUniqueWithValues(self.ticket, [('name', '=', 'First ticket')],
                                        dict(parent_id=self.project_id))

            # checking both search and read perms in one shot:
            self.assertUniqueWithValues(bouquet, [], dict(name=u"Un bouquet ?"))
