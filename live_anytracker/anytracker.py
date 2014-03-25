# -*- coding: utf-8 -*-

from openerp.osv import osv


class AnytrackerTicket(osv.Model):

    _name = 'anytracker.ticket'

    _inherit = [
        'anytracker.ticket',
        'abstract.live',
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
