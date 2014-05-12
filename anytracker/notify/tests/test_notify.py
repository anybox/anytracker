from anybox.testing.openerp import SharedSetupTransactionCase
from os.path import join


class TestNotify(SharedSetupTransactionCase):

    _module_ns = 'anytracker'
    _data_files = (join('..', '..', 'tests', 'data.xml'),)

    @classmethod
    def initTestData(cls):
        super(TestNotify, cls).initTestData()
        cr, uid = cls.cr, cls.uid
        cls.tickets = cls.registry('anytracker.ticket')
        cls.notifys = cls.registry('anytracker.complexity')
        cls.user = cls.registry('res.users')
        cls.ratings = cls.registry('anytracker.rating')
        cls.stages = cls.registry('anytracker.stage')
        cls.mails = cls.registry('mail.mail')

        cls.member_id = cls.user.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_member'),
                            cls.ref('base.group_user')])]})
        cls.customer_id = cls.user.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [cls.ref('anytracker.group_customer')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        method = self.ref('anytracker.method_test')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.tickets.create(cr, uid,
                                         {'name': 'Test',
                                          'participant_ids': [(6, 0, participant_ids)],
                                          'method_id': method})
        return project_id

    def test_notify(self):
        """ Check notifications
        """
        cr, uid = self.cr, self.uid
        # create a project with a team of 3 people
        project_id = self.createProject([self.customer_id, self.member_id])
        # we set the todo column as notifying
        self.stages.write(cr, uid,
                          [self.ref('anytracker.stage_test_todo')],
                          {'notify': True,
                           'notify_multiple': True,
                           'notify_template_id': self.ref('anytracker.email_template_test')})
        # we check the number of mails in the queue
        nb_mails = self.mails.search(cr, uid, [], count=True)
        # create a ticket
        ticket_id = self.tickets.create(cr, uid,
                                        {'name': 'notifying ticket',
                                         'parent_id': project_id, },
                                        context={'active_id': project_id})
        # we should now have one more message
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 1)

        # now we move the ticket to another column which should notify as well
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_test_todo')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 2)

        # If we move the column to the initial column it won't notify again
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_test_draft')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 2)

        # if we move the ticket to the ever-notifying column, it will notify again
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_test_todo')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 3)

        # if we move the ticket to a non-notifying column, it won't notify
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_test_done')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 3)

        # we set the 1st column as urgent and we set a sender email so that email is sent
        self.stages.write(cr, uid,
                          self.ref('anytracker.stage_test_draft'),
                          {'notify_urgent': True})
        self.user.write(cr, uid, self.member_id, {'email': 'test@example.com'})
        # then we create another ticket
        urgent_ticket_id = self.tickets.create(cr, uid,
                                               {'name': 'urgent notifying ticket',
                                                'parent_id': project_id, },
                                               context={'active_id': project_id})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 4)
        self.assertEquals(
            len(self.tickets.browse(cr, uid, urgent_ticket_id).notified_stage_ids), 1)

        # we move forth and back the ticket, we shouldn't have another notification
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_test_done')})
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_test_draft')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 4)
        self.assertEquals(
            len(self.tickets.browse(cr, uid, urgent_ticket_id).notified_stage_ids), 1)
