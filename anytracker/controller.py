import werkzeug.utils

from odoo import http

from odoo.addons.web.controllers.main import request, abort_and_redirect, Home


class SetUrlMixin(object):
    def set_url(
            self,
            path,
            view_type,
            model,
            id=False,
            action_xml_id='anytracker.act_all_tasks'
        ):
        assert action_xml_id  # if no action un url param odoo will redirect again to other url!
        action = request.env.ref(action_xml_id)
        action_id = action and action.id or False

        url = '{path}#{id}view_type={view_type}&model={model}'.format(
            path=path,
            id=id and 'id={id}&'.format(id=id) or '',
            view_type=view_type,
            model=model
        )
        if action_id:
            url += '&action={action_id}'.format(action_id=action_id)
        return url


class LoginHome(SetUrlMixin, Home):
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
                redirect = self.set_url('/web', 'list', 'anytracker.ticket')

        return super(LoginHome, self)._login_redirect(uid, redirect=redirect)


class UrlDirection(SetUrlMixin, http.Controller):
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
        # Example: http://localhost:8069/anytracker/anytracker11/ticket/7
        if db is None or meth is None or id is None:
            return self._anytracker_error()
        model = self.__class__.method_model_map.get(meth)
        if model is None:
            return self._anytracker_error()
        return self._dispatch_anytracker(db, model, id)

    def _dispatch_anytracker(self, db, model, id):
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

        url = self.set_url('/web', 'form', model, id=id)

        if same_db:
            return werkzeug.utils.redirect(url)
        abort_and_redirect(url)  # other db

    def _anytracker_error(self):
        # TODO GR: issue a proper code 400
        return ("Bad query\nUse : /anytracker/method/methparams\n"
                "with method one of: " + ', '.join(self.__class__.method_model_map.keys()))
