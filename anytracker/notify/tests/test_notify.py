from anybox.testing.openerp import SharedSetupTransactionCase


class TestNotify(SharedSetupTransactionCase):

    _module_ns = 'anytracker'

    @classmethod
    def initTestData(self):
        super(TestNotify, self).initTestData()
        cr, uid = self.cr, self.uid
        self.tickets = self.registry('anytracker.ticket')
        self.notifys = self.registry('anytracker.complexity')
        self.user = self.registry('res.users')
        self.ratings = self.registry('anytracker.rating')
        self.mails = self.registry('mail.mail')

        self.member_id = self.user.create(
            cr, uid,
            {'name': 'Member',
             'login': 'member',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_member'),
                            self.ref('base.group_user')])]})
        self.customer_id = self.user.create(
            cr, uid,
            {'name': 'Customer',
             'login': 'customer',
             'groups_id': [(6, 0,
                           [self.ref('anytracker.group_customer')])]})

    def createProject(self, participant_ids):
        cr, uid = self.cr, self.uid
        quickstart_method = self.ref('anytracker.method_quickstart')
        if isinstance(participant_ids, int) or isinstance(participant_ids, long):
            participant_ids = [participant_ids]
        project_id = self.tickets.create(cr, uid,
                                         {'name': 'Quickstart test',
                                          'participant_ids': [(6, 0, participant_ids)],
                                          'method_id': quickstart_method})
        return project_id

    def test_notify(self):
        """ Check notifications
        """
        cr, uid = self.cr, self.uid
        # create a project with a team of 3 people
        project_id = self.createProject([self.customer_id, self.member_id])
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
                           {'stage_id': self.ref('anytracker.stage_quickstart_todo')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 2)

        # If we move the column to the initial column it won't notify again
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_quickstart_draft')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 2)

        # if we move the ticket to the ever-notifying column, it will notify again
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_quickstart_todo')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 3)

        # if we move the ticket to a non-notifying column, it won't notify
        self.tickets.write(cr, uid, [ticket_id],
                           {'stage_id': self.ref('anytracker.stage_quickstart_done')})
        self.assertEquals(self.mails.search(cr, uid, [], count=True) - nb_mails, 3)
