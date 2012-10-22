# -*- coding: utf-8 -*-

from osv import osv
from osv import fields


class Ticket(osv.Model):

    _inherit = 'anytracker.ticket'
    _columns = {
            'assigned_id': fields.many2one('res.users',
                 'Assigned to'),
              }
