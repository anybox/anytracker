import time
from osv import osv, fields


class Comment(osv.Model):
    """Represents a comment
    """
    _name = 'anytracker.comment'
    _description = u'A comment attached to a ticket'
    _order = 'date DESC'
    _columns = {
        'ticket_id': fields.many2one('anytracker.ticket', u'Ticket', required=True),
        'date': fields.datetime(u'Date', required=True),
        'user_id': fields.many2one('res.users', u'User', required=True),
        'text': fields.text(u'Comment'),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context, **kw: uid,
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }


class Ticket(osv.Model):
    """Add comments to tickets
    """
    _inherit = 'anytracker.ticket'

    _columns = {
        'comment_ids': fields.one2many('anytracker.comment', 'ticket_id', u'Comments'),
    }
