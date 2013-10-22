# coding: utf-8

from openerp.addons.web import http
import werkzeug.utils
from openerp import pooler, SUPERUSER_ID as uid
from urlparse import urljoin
from urllib import urlencode


class UrlDirection(http.Controller):
    _cp_path = '/anytracker'

    @http.httprequest
    def __ticket(self, request):
        # extract db and ticket number from URL
        path = request.httprequest.path[1:].split('/')
        url = "/web/webclient/home/#"
        if len(path) != 4 or path[2] != 'ticket':
            return "Bad query\nUse : /anytracker/`db`/ticket/`ticket number`"
        db = path[1]
        try:
            pool = pooler.get_pool(db)
        except Exception, e:
            return "%r" % (e,)

        # retrieve the ticket
        number = path[-1]
        cr = pooler.get_db(db).cursor()
        ticket_obj = pool.get('anytracker.ticket')
        ticket_ids = ticket_obj.search(cr, uid, [('number', '=', int(number))])
        if not ticket_ids:
            return "Bad ticket number %r" % number
        ticket_id = ticket_ids[0]

        # contruct the new URL
        query = {'db': db}
        fragment = {
            'model': 'anytracker.ticket',
            'id': str(ticket_id),
        }
        base_url = pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        url = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        redirect = werkzeug.utils.redirect(url, 302)
        redirect.autocorrect_location_header = False
        return redirect

    def __getattr__(self, func_name):
        return self.__ticket
