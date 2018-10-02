import werkzeug.utils

from odoo import http

from odoo.addons.web.controllers.main import request, abort_and_redirect, Home


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
    # TODO append anytracker menu_id= in url
    method_model_map = dict(
        ticket='anytracker.ticket',
        bouquet='anytracker.bouquet'
    )

    @http.route(
        '/anytracker/<string:db>/<string:meth>/<int:id>',
        type='http',
        auth='user',
        website=True
    )
    def dispatch_anytracker(self, meth=None, db=None, id=None, *args, **kw):
        # Example: http://localhost:8069/anytracker/ticket/24
        if db is None or meth is None or id is None:
            return self._anytracker_error()
        model = self.__class__.method_model_map.get(meth)
        if model is None:
            return self._anytracker_error()
        return self.dispatch(db, model, id)

    def dispatch(self, db, model, id):
        same_db = True

        if db != request.session.db:
            request.session.db = db
            same_db = False

        if model == 'anytracker.ticket':
            # ticket identified by number versus id
            ticket_recset = request.env[model].search([('number', '=', int(id))])
            if not ticket_recset:
                return "Bad ticket number %r" % id
            id = ticket_recset[0].id

        url = '/web#id={id}&view_type=form&model={model}'.format(
            id=id,
            model=model,
        )

        if same_db:
            return werkzeug.utils.redirect(url)
        abort_and_redirect(url)  # other db

    def _anytracker_error(self):
        # TODO GR: issue a proper code 400
        return ("Bad query\nUse : /anytracker/method/methparams\n"
                "with method one of: " + ', '.join(self.__class__.method_model_map.keys()))
