from urllib.parse import urljoin
from urllib.parse import urlencode
import werkzeug.utils

from odoo import http
from odoo import SUPERUSER_ID as uid

from odoo.addons.web.controllers.main import Home
from odoo.addons.web.controllers.main import request


class LoginHome(Home):
    def _login_redirect(self, uid, redirect=None):
        """
        #11435 patch login redirection

        Since v11, for portal user or user not tied to a legacy sel_groups category like
        Employee, Accounting invoicing, etc, user is auto redirected to portal: /my route.

        For a user of anytracker 'customer' group, redirect to '/web' to access backlog
        and AnyTracker menus.
        """
        if request.env and request.env.user and len(request.env.user.groups_id) > 0:
            anytracker_customer_group = request.env.ref('anytracker.group_customer')
            if anytracker_customer_group \
                and anytracker_customer_group.id in request.env.user.groups_id.ids:
                    redirect = '/web'

        return super(LoginHome, self)._login_redirect(uid, redirect=redirect)


class UrlDirection(http.Controller):
    @http.route(
        '/anytracker/<string:db>/<string:meth>/<int:number>', type='http',
        auth='user', website=True
    )
    def dispatch_anytracker(self, db=None, meth=None, number=None, *args, **kw):
        # Sample : http://localhost:8069/anytracker/anytraker_002/ticket/24
        if db is None and meth is None and number is None:
            return self._anytracker_error()
        meth = self.dispatcher_methods.get(meth)
        if meth is None:
            return self._anytracker_error()
        # try:
        #    pool = pooler.get_pool(db)
        # except Exception as e:
        #    return "%r" % (e,)
        # cr = pooler.get_db(db).cursor()
        # return meth(self, db, cr, pool, [number])

    def dispatch_ticket(self, db_name, cr, pool, segments):
        if len(segments) != 1:
            return "Error: there should be exactly one param for 'ticket': the number"

        # retrieve the ticket
        number = segments[0]
        ticket_obj = pool.get('anytracker.ticket')
        ticket_ids = ticket_obj.search(cr, uid, [('number', '=', int(number))])
        if not ticket_ids:
            return "Bad ticket number %r" % number
        ticket_id = ticket_ids[0]

        # contruct the new URL
        query = {'db': db_name}
        fragment = {
            'model': 'anytracker.ticket',
            'id': str(ticket_id),
        }
        base_url = '/web/'
        url = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        werkzeug.utils.redirect(url, 302)
        # redirect.autocorrect_location_header = False
        print(url)
        return werkzeug.utils.redirect(url)

    def dispatch_bouquet(self, db_name, cr, pool, segments):
        if len(segments) != 1:
            return "Error: there should be exactly one param for 'bouquet': its id"

        # contruct the new URL
        query = {'db': db_name}
        fragment = {
            'model': 'anytracker.bouquet',
            'id': segments[0],
        }
        base_url = '/web/'
        url = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        redirect = werkzeug.utils.redirect(url, 302)
        redirect.autocorrect_location_header = False
        return redirect

    def __getattr__(self, func_name):
        #     TODO GR: I'm sure there's better than this manual dispatching (no time to check
        #     this works well enough for now)
        return self.dispatcher_methods

    dispatcher_methods = dict(ticket=dispatch_ticket,
                              bouquet=dispatch_bouquet)

    def _anytracker_error(self):
        # TODO GR: issue a proper code 400
        return ("Bad query\nUse : /anytracker/`db`/submethod/methparams\n"
                "    with submethod one of: " + ', '.join(self.dispatcher_methods.keys()))
