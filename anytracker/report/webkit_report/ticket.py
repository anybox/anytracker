# -*- coding: utf-8 -*-
from openerp.report import report_sxw
from .CommonParser import CommonParser


class TicketReport(CommonParser):
    def __init__(self, cr, uid, name, context):
        super(TicketReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'test_methode': self._test_methode,
                                  'displayLocaleDateTime': self._displayLocaleDateTime,
                                  })

    def _test_methode(self):
        return False

report_sxw.report_sxw('report.ticket_webkit',
                      'anytracker.ticket',
                      'anytracker/report/webkit_report/ticket.mako',
                      parser=TicketReport)
