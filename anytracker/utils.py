import mock


def fake_mail_message_creation(func):
    def patched_function():
        with mock.patch('openerp.addons.mail.mail_message.mail_message.create', return_value=True):
            return func
    return patched_function
