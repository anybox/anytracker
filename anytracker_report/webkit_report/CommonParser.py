# -*- coding: utf-8 -*-
from openerp.report import report_sxw
from openerp.tools.translate import _
from datetime import datetime
from openerp.tools import misc
from openerp.osv import osv
import pytz


class CommonParser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(CommonParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'displayLocaleDateTime': self._displayLocaleDateTime,
                                  })

    def _displayLocaleDateTime(self, timezone, format='%d/%m/%Y %H:%M', server_tz=None):
        try:
            if not server_tz:
                server_tz = misc.get_server_timezone()
            return pytz.timezone(server_tz).localize(datetime.now()).astimezone(
                pytz.timezone(timezone)).strftime(format)
        except:
            raise osv.except_osv(_('Timezone error or date format invalid!'),
                                 _('Please set your timezone before to generate this report.') +
                                 _(' One of those values is not valid: timezone= %r - format= %r')
                                 % (timezone, format))
