from anybox.testing.openerp import SharedSetupTransactionCase


class TestBouquets(SharedSetupTransactionCase):

    @classmethod
    def create_project(cls, participant_ids, **kw):
        """Create a project with given participants and some default values.

        :param kw: additional field values, will override the default ones.
        """
        vals = dict(name="Test project", method_id=cls.ref('anytracker.method_scrum'),
                    participant_ids=[(6, 0, participant_ids)])
        vals.update(kw)
        return cls.ticket.create(cls.cr, cls.uid, vals)

    @classmethod
    def create_bouquet(cls, ticket_ids, **kw):
        """Create a bouquet with given tickets and some default values.

        :param kw: additional field values, will override the default ones.
        """
        vals = dict(name="Test bouquet", method_id=cls.ref('anytracker.method_scrum'),
                    ticket_ids=[(6, 0, ticket_ids)])
        vals.update(kw)
        return cls.bouquet.create(cls.cr, cls.uid, vals)

    @classmethod
    def initTestData(cls):
        super(TestBouquets, cls).initTestData()

        cr, uid = cls.cr, cls.uid
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

        cls.admin_id = cls.uid

    def test_create_read(self):
        tids = self.ticket_ids
        self.assertRecord(self.bouquet, self.bouquet_id,
                          dict(ticket_ids=set(tids),
                               nb_tickets=len(tids),
                               project_ids=set([self.project_id])),
                          list_to_set=True)

    def test_create_read_perm(self):
        """Switch to non-privileged user to check access."""
        for tested_uid in (self.member_id, self.customer_id):
            self.uid = tested_uid
            # if this fails, fix the main part of Anytracker first (no other unit tests at this
            # time of writing):
            self.assertUniqueWithValues(self.ticket, [('name', '=', 'First ticket')],
                                        dict(parent_id=self.project_id))

            # checking both search and read perms in one shot:
            self.assertUniqueWithValues(self.bouquet, [], dict(name=u"Un bouquet ?"))

    def test_read_perm_non_participating(self):
        # first, let's remove our 2 users from the related project
        self.ticket.write(self.cr, self.admin_id, self.project_id,
                          dict(participant_ids=[(6, 0, [])]))

        self.uid = self.member_id
        self.assertNoRecord(self.bouquet, [])

    def test_read_perm_participating_mixed(self):
        """A user participating in any project related to the bouquet must have right perm."""
        p2id = self.create_project([], name="Another Project")  # no participant
        self.ticket.write(self.cr, self.admin_id, self.ticket_ids[0], dict(parent_id=p2id))

        # testing the project_ids function field while we're at it
        self.assertRecord(self.bouquet, self.bouquet_id,
                          dict(project_ids=set([self.project_id, p2id])),
                          list_to_set=True)

        for tested_uid in (self.member_id, self.customer_id):
            self.uid = tested_uid

            # bouquet is still visible by user, although one of its tickets is not
            self.assertEqual(self.searchUnique(self.bouquet, []), self.bouquet_id)
            self.assertNoRecord(self.ticket, [('id', '=', self.ticket_ids[0])])

    def test_participant_ids(self):
        # just a very simple case, but better than nothing
        self.assertRecord(self.bouquet, self.bouquet_id,
                          dict(participant_ids=set([self.member_id, self.customer_id])),
                          list_to_set=True)

    def test_get_rating(self):
        self.ticket.write(self.cr, self.uid, self.ticket_ids, {'rating': '2.0'})
        self.assertEquals(self.bouquet.browse(self.cr, self.uid, self.bouquet_id).bouquet_rating,
                          4.0)

    def test_create_member(self):
        """Any member can create a bouquet."""
        self.bouquet.create(self.cr, self.member_id, dict(name='member bouquet'))
        self.bouquet.create(self.cr, self.member_id, dict(name='member bouquet',
                                                          ticket_ids=self.ticket_ids))
