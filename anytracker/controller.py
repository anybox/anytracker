# -*- coding: utf-8 -*-

from openerp.addons.web.common import http
import werkzeug.utils
from openerp import pooler, SUPERUSER_ID


class UrlDirection(http.Controller):
    _cp_path = '/anytracker'

    @http.httprequest
    def __ticket(self, request):
        path = request.httprequest.path[1:].split('/')
        url = "/web/webclient/home/#"
        if len(path) != 4 or path[2] != 'ticket':
            return "Bad query\nUse : /anytracker/`db`/ticket/`ticket number`"
        db = path[1]
        try:
            pool = pooler.get_pool(db)
        except Exception, e:
            return "%r" % (e,)
        ticket = path[-1]
        cursor = pooler.get_db(db).cursor()
        ticket_obj = pool.get('anytracker.ticket')
        domain = [
            ('number', '=', int(ticket)),
        ]
        ticket_ids = ticket_obj.search(cursor, SUPERUSER_ID, domain)
        if not ticket_ids:
            return "Bad ticket number %r" % ticket
        data_obj = pool.get('ir.model.data')
        action_id = data_obj.get_object_reference(
            cursor, SUPERUSER_ID, 'anytracker', 'act_all_tasks')[1]
        val = [
            ('id',  str(ticket_ids[0])),
            ('view_type', 'page'),
            ('model', 'anytracker.ticket'),
            ('action_id', str(action_id)),
        ]
        # FIXME: just below use urllib.urlencode
        url += '&'.join(v[0] + "=" + v[1] for v in val)
        redirect = werkzeug.utils.redirect(url, 302)
        redirect.autocorrect_location_header = False
        return redirect

    def __getattr__(self, func_name):
        return self.__ticket

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
