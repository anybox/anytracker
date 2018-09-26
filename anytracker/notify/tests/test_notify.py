# coding: utf-8
from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join


class TestNotify(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestNotify, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.TICKET = cls.env['anytracker.ticket']
        cls.USER = cls.env['res.users']
        cls.STAGE = cls.env['anytracker.stage']
        cls.MAIL = cls.env['mail.mail']

        recset = cls.USER.search([('login', '=', 'member')])
        cls.member_id = recset and recset[0].id or cls.USER.create(
            {'name': 'Member',
             'login': 'member',
             'email': 'member@localhost',
             'groups_id':
                [(6, 0, [cls.ref('anytracker.group_member'),
                         cls.ref('base.group_user')])]}
        ).id

        recset = cls.USER.search([('login', '=', 'member2')])
        cls.member2_id = recset and recset[0].id or cls.USER.create(
            {'name': 'Member2',
             'login': 'member2',
             'email': 'member2@localhost',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]}
        ).id

        recset = cls.USER.search([('login', '=', 'customer')])
        cls.customer_id = recset and recset[0].id or cls.USER.create(
            {'name': 'Customer',
             'login': 'customer',
             'email': 'customer@localhost',
             'groups_id': [(6, 0, [cls.ref('anytracker.group_customer')])]}
        ).id

    def test_notify(self):
        """ Check notifications.
        """
        # create a project with a team of 3 people
        project = self.TICKET.create({
            'name': 'Test',
            'participant_ids': [(6, 0, [self.customer_id, self.member_id])],
            'method_id': self.ref('anytracker.method_test')})
        # we set the todo column as notifying
        self.STAGE.browse(self.ref('anytracker.stage_test_todo')).write({
            'notify': True,
            'notify_multiple': True,
            'notify_template_id': self.ref('anytracker.email_template_test')})
        # we check the number of mails in the queue
        nb_mails = self.MAIL.search([], count=True)
        # create a ticket
        ticket = self.TICKET.with_context({'active_id': project.id}).create({
            'name': 'notifying ticket',
            'parent_id': project.id, })
        # we should now have one more message
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 1)

        # now we move the ticket to another column which should notify as well
        ticket.write({'stage_id': self.ref('anytracker.stage_test_todo')})
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 2)

        # If we move the column to the initial column it won't notify again
        ticket.write({'stage_id': self.ref('anytracker.stage_test_draft')})
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 2)

        # if we move ticket to the ever-notifying column, it will notify again
        ticket.write({'stage_id': self.ref('anytracker.stage_test_todo')})
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 3)

        # if we move the ticket to a non-notifying column, it won't notify
        ticket.write({'stage_id': self.ref('anytracker.stage_test_done')})
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 3)

        # we set the 1st column as urgent & set an email so that email is sent
        self.STAGE.browse(self.ref('anytracker.stage_test_draft')).write({
            'notify_urgent': True})
        self.USER.browse(self.member_id).write({'email': 'test@example.com'})

        # then we create another ticket (default stage = 'draft' mail is sended right away)
        urgent = self.TICKET.with_context({'active_id': project.id}).create({
            'name': 'urgent notifying ticket',
            'parent_id': project.id, })
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 3)
        self.assertEquals(len(urgent.notified_stage_ids), 1)

        # we move forth and back the ticket, we shouldn't have more notif
        ticket.write({'stage_id': self.ref('anytracker.stage_test_done')})
        ticket.write({'stage_id': self.ref('anytracker.stage_test_draft')})
        self.assertEquals(self.MAIL.search([], count=True) - nb_mails, 3)
        self.assertEquals(len(urgent.notified_stage_ids), 1)

    def test_participants(self):
        """ability for members to freely join and leave the projects
        """
        # the member creates a project with himself as a participant
        project = self.TICKET.sudo(self.member_id).create(
            {'name': 'Project1',
             'method_id': self.ref('anytracker.method_test')})
        # we check the number of followers (users notified)
        self.assertEquals(len(project.message_follower_ids), 1)

        # the member adds the customer
        project.sudo(self.member_id).write(
            {'participant_ids': [(6, 0, [self.customer_id, self.member_id])]})
        self.assertEquals(len(project.message_follower_ids), 2)

        # the customer is not allowed to add participants
        # self.assertRaises(
        #    except_orm,
        #    project.sudo(self.member_id).write,
        #    {'participant_ids': [(6, 0, [self.customer_id, self.member_id])]})
        # self.assertEquals(len(project.message_follower_ids), 2)

        # the member2 choose to join the project again, he's notified
        project.sudo(self.member2_id).join_project()
        self.assertEquals(len(project.message_follower_ids), 3)

        # the customer creates a ticket
        ticket = self.TICKET.sudo(self.customer_id).with_context(
            {'active_id': project.id}).create({
                'name': 'notifying ticket',
                'parent_id': project.id, })
        self.assertEquals(len(ticket.message_follower_ids), 3)

        # the member2 chooses to leave the project, he's no more notified
        project.sudo(self.member2_id).leave_project()
        self.assertEquals(len(project.message_follower_ids), 2)
        self.assertEquals(len(ticket.message_follower_ids), 2)

        # the member2 chooses to receive notifications on the project
        project.sudo(self.member2_id).message_subscribe_users(
            [self.member2_id])
        self.assertEquals(len(project.message_follower_ids), 3)
        self.assertEquals(len(ticket.message_follower_ids), 3)

        # the customer creates a ticket
        ticket2 = self.TICKET.sudo(self.customer_id).with_context(
            {'active_id': project.id}).create({
                'name': 'notifying ticket',
                'parent_id': project.id, })
        # member2 is notified, even if not participant
        self.assertEquals(len(ticket2.message_follower_ids), 3)
