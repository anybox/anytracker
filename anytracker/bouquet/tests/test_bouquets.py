# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase


class TestBouquets(SharedSetupTransactionCase):

    @classmethod
    def initTestData(cls):
        super(TestBouquets, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.BOUQUET = cls.env['anytracker.bouquet']
        #cls.ticket_obj = cls.registry['anytracker.ticket']
        cls.ticket_obj = cls.TICKET
        # cls.bouquet_obj = cls.registry['anytracker.bouquet']
        cls.bouquet_obj = cls.BOUQUET
        # we delete this bouquet because it makes test fails (when using database backup)
        bouquet_sprint_mlf = cls.BOUQUET.search([('name', '=', u'Sprint MLF: juillet')])
        if bouquet_sprint_mlf:
            bouquet_sprint_mlf.unlink()

        USER = cls.env['res.users']

        recset = USER.search([('login', '=', 'at.user')])
        cls.member_id = recset and recset[0].id or USER.create({
            'name': 'anytracker member',
            'login': 'at.user',
            'email': 'member@localhost',
            'groups_id': [(6, 0, [cls.ref('base.group_user'), cls.ref('anytracker.group_member')])],
        }).id

        recset = USER.search([('login', '=', 'at.cust')])
        cls.customer_id = recset and recset[0].id or USER.create({
            'name': "anytracker customer",
            'login': 'at.cust',
            'email': 'customer@localhost',
            'groups_id': [(6, 0, [
                # FIXME: base.group_user actually needed exclusively during u test
                # for 'mail.activity.mixin' fields with groups='base.group_user'
                # during ticket write
                # (in real case ticket is writable without base.group_user)
                cls.ref('base.group_user'),
                cls.ref('anytracker.group_customer')])],
        }).id

        recset = USER.search([('login', '=', 'at.part')])
        cls.partner_id = recset and recset[0].id or USER.create({
            'name': "anytracker partner",
            'login': 'at.part',
            'email': 'partner@localhost',
            'groups_id': [(6, 0, [
                cls.ref('anytracker.group_partner')])],
        }).id

        cls.project = cls.TICKET.create({
            'name': "Main test project",
            'method_id': cls.ref('anytracker.method_scrum'),
            'participant_ids': [(6, 0, [cls.member_id, cls.customer_id, cls.partner_id])],
        })
        cls.ticket1 = cls.TICKET.create({
            'name': "First ticket",
            'parent_id': cls.project.id,
        })
        cls.ticket2 = cls.TICKET.create({
            'name': "Second ticket",
            'parent_id': cls.project.id,
        })
        cls.tickets = cls.ticket1 + cls.ticket2
        cls.bouquet = cls.BOUQUET.create({
            'name': u"Un bouquet ?",
            'ticket_ids': [(6, 0, cls.tickets.ids)]})
        cls.bouquet_domain = [('name', '=', u"Un bouquet ?")]

        cls.admin_id = cls.uid

    def test_create_read(self):
        self.assertRecord(
            self.bouquet_obj, self.bouquet.id, {
                'ticket_ids': set(self.tickets.ids),
                'nb_tickets': len(self.tickets.ids),
                'project_ids': set([self.project.id]),
            }, list_to_set=True
        )

    def test_create_read_perm(self):
        """Switch to non-privileged user to check access."""
        for uid in (self.member_id, self.customer_id, self.partner_id):
            self.uid = uid
            # if this fails, fix the main part of Anytracker first
            # (no other unit tests at this time of writing):
            self.assertUniqueWithValues(
                self.ticket_obj, [('name', '=', "First ticket")], {'parent_id': self.project.id}
            )
            # checking both search and read perms in one shot:
            self.assertUniqueWithValues(
                self.bouquet_obj, self.bouquet_domain, {'name': u"Un bouquet ?"}
            )

    def test_read_perm_non_participating(self):
        # first add at least one ticket
        self.uid = self.member_id
        self.project.sudo(self.admin_id).write(
            {
                'ticket_ids': [(4, [self.ticket1.id])],
            }
        )
        res = self.BOUQUET.search([])
        self.assertTrue(res)
        # second, let's remove our 2 users from the related project
        self.project.sudo(self.admin_id).write(
            {
                'participant_ids': [(6, 0, [])]
            }
        )
        self.assertNoRecord(self.bouquet_obj, self.bouquet_domain)

    def test_read_perm_participating_mixed(self):
        """A user participating in any project related to the bouquet
        must have right perm.
        """
        project = self.TICKET.sudo(self.member_id).create({
            'name': "Another Project",  # no participants
            'method_id': self.ref('anytracker.method_scrum')})
        self.ticket1.sudo().write({'parent_id': project.id})

        # testing the project_ids function field while we're at it
        self.assertRecord(
            self.bouquet_obj,
            self.bouquet.id,
            {'project_ids': set([self.project.id, project.id])},
            list_to_set=True)

        # bouquet is still visible by the member,
        # although one of its tickets is not
        self.uid = self.member_id
        self.assertEqual(
            self.searchUnique(self.bouquet_obj, self.bouquet_domain),
            self.bouquet.id)
        self.assertEqual(
            1, len(self.TICKET.search([('id', '=', self.ticket1.id)])))
        # bouquet is still visible by the customer,
        # although one of its tickets is not
        self.uid = self.customer_id
        self.assertEqual(
            self.searchUnique(self.bouquet_obj, self.bouquet_domain),
            self.bouquet.id)
        self.assertNoRecord(
            self.ticket_obj,
            [('id', '=', self.ticket1.id)])
        # same for partner
        self.uid = self.partner_id
        self.assertEqual(
            self.searchUnique(self.bouquet_obj, self.bouquet_domain),
            self.bouquet.id)
        self.assertNoRecord(
            self.ticket_obj,
            [('id', '=', self.ticket1.id)])

    def test_participant_ids(self):
        # just a very simple case, but better than nothing
        self.assertRecord(
            self.bouquet_obj, self.bouquet.id,
            {'participant_ids':
                set([self.admin_id, self.member_id, self.customer_id, self.partner_id])},
            list_to_set=True)

    def test_get_rating(self):
        self.tickets.write({'rating': '2.0'})
        self.assertEquals(self.bouquet.bouquet_rating, 4.0)

    def test_create_member(self):
        """Any member can create a bouquet.
        """
        self.BOUQUET.sudo(self.member_id).create({
            'name': 'member bouquet'})
        self.BOUQUET.sudo(self.member_id).create({
            'name': 'member bouquet',
            'ticket_ids': [(6, 0, self.tickets.ids)]})
