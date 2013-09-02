# coding: utf-8
from osv import fields, osv
from tools.translate import _


class Ticket(osv.Model):

    _name = 'anytracker.ticket'
    _description = "Anytracker tickets"
    _rec_name = 'breadcrumb'
    _order = 'create_date DESC'

    def _get_siblings(self, cr, uid, ids, field_name, args, context=None):
        """ get tickets at the same hierachical level
        """
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            domain = [
                ('parent_id', '=', ticket.parent_id.id),  # the same parent
                ('id', '!=', ticket.id),  # not me
            ]
            res[ticket.id] = self.search(cr, uid, domain, context=context)
        return res

    def _shorten_description(self, cr, uid, ids, field_name, args, context=None):
        """shortened description
        """
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            descr = ticket.description or ''
            res[ticket.id] = descr[:200] + u'(…)' if len(descr) > 200 else descr
        return res

    def _kanban_description(self, cr, uid, ids, field_name, args, context=None):
        """shortened description for the kanban
        """
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            lines = (ticket.description or '').splitlines()
            if len(lines) > 5:
                lines = lines[:5]
                lines.append(u'(…)')
            res[ticket.id] = '<br/>'.join(lines)
        return res

    def _breadcrumb(self, cr, uid, ids, context=None):
        """ get all the parents until the root ticket
        """
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            breadcrumb = [ticket]
            current_ticket = ticket
            while current_ticket.parent_id:
                breadcrumb.insert(0, current_ticket.parent_id)
                current_ticket = current_ticket.parent_id
            res[ticket.id] = breadcrumb
        return res

    def _formatted_breadcrumb(self, cr, uid, ids, field_name, args, context=None):
        """ format the breadcrumb
        TODO : format in the view (in js)
        """
        res = {}
        for i, breadcrumb in self._breadcrumb(cr, uid, ids, context).items():
            res[i] = u' / '.join([b.name for b in breadcrumb])
        return res

    def _get_admin_id(self, cr, uid, context=None):
        xml_pool = self.pool.get('ir.model.data')
        res_users = self.pool.get('res.users')
        admin_group_id = xml_pool.get_object_reference(cr, uid, 'base', 'group_erp_manager')[1]
        domain = [
            ('groups_id', "in", [admin_group_id]),
        ]
        admin_ids = res_users.search(cr, uid, domain, context=context)
        if admin_ids:
            return admin_ids[0]
        raise osv.except_osv(_('Error'), _('No user with ERP Manager group found'))

    def _set_project(self, cr, uid, ticket_id, context=None):
        """store the root ticket (the project) in the ticket
        Should be more efficient than looking up the project everytime
        """
        ticket = self.browse(cr, uid, ticket_id, context)
        parent_id = ticket.parent_id and ticket.parent_id.id
        if parent_id:
            breadcrumb = self._breadcrumb(cr, uid, [parent_id], context)[parent_id]
            if not breadcrumb:
                breadcrumb = [self.browse(cr, uid, parent_id)]
            project_id = breadcrumb[0].id
        else:
            # if no parent, we are the project
            project_id = ticket_id
        super(Ticket, self).write(cr, uid, ticket_id, {'project_id': project_id}, context)

    def write(self, cr, uid, ids, values, context=None):
        """write the project_id when writing the parent
        """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        res = super(Ticket, self).write(cr, uid, ids, values, context=context)
        for ticket_id in ids:
            # set the project of the ticket
            self._set_project(cr, uid, ticket_id, context)
        return res

    def _get_permalink(self, cr, uid, ids, field_name, args, context=None):
        base_uri = '/anytracker/%s/ticket/' % cr.dbname
        return dict((r['id'], base_uri + str(r['number']))
                    for r in self.read(cr, uid, ids, ('number',)))

    def create(self, cr, uid, values, context=None):
        """write the project_id when writing the parent
        """
        values.update({
            'number': self.pool.get('ir.sequence').next_by_code(cr, self._get_admin_id(cr, uid),
                                                                'anytracker.ticket'),
        })
        ticket_id = super(Ticket, self).create(cr, uid, values, context=context)
        # set the project of the ticket
        self._set_project(cr, uid, ticket_id, context)

        return ticket_id

    def _default_parent_id(self, cr, uid, context=None):
        """Return the current ticket of the parent if this is a leaf
        """
        ticket_pool = self.pool.get('anytracker.ticket')
        active_id = context.get('active_id')
        if not active_id:
            return False
        ticket = ticket_pool.browse(cr, uid, active_id)
        if not ticket.parent_id:
            return active_id
        elif not ticket.child_ids:
            return ticket.parent_id.id
        else:
            return active_id

    def _default_project_id(self, cr, uid, context=None):
        """Return the same project as the active_id
        """
        ticket_pool = self.pool.get('anytracker.ticket')
        active_id = context.get('active_id')
        if not active_id:
            return False
        ticket = ticket_pool.browse(cr, uid, active_id)
        if not ticket.parent_id:
            return active_id
        else:
            return ticket.project_id.id

    def _nb_children(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for i in ids:
            nb_children = self.search(cr, uid, [('id', 'child_of', i)], count=True)
            res[i] = nb_children
        return res

    def _search_breadcrumb(self, cr, uid, obj, field, domain, context=None):
        """Use the 'name' in the search function for the parent,
        instead of 'breadcrum' which is implcitly used because of the _rec_name
        """
        assert(len(domain) == 1 and len(domain[0]) == 3)  # handle just this case
        (f, o, v) = domain[0]
        return [('name', o, v)]

    def onchange_parent(self, cr, uid, ids, parent_id, context=None):
        """ Fill the method when changing parent
        """
        context = context or {}
        if not parent_id:
            return {}
        method_id = self.read(cr, uid, parent_id, ['method_id'],
                              context, load='_classic_write')['method_id']
        return {'value': {'method_id': method_id}}

    _columns = {
        'name': fields.char('Title', 255, required=True),
        'number': fields.integer('Number'),
        'permalink': fields.function(_get_permalink, type='string', string='Permalink',
                                     obj='anytracker.ticket', method=True),
        'description': fields.text('Description', required=False),
        'create_date': fields.datetime('Creation Time'),
        'write_date': fields.datetime('Modification Time'),
        'shortened_description': fields.function(
            _shorten_description,
            type='text',
            obj='anytracker.ticket',
            string='Description'),
        'kanban_description': fields.function(
            _kanban_description,
            type='text',
            obj='anytracker.ticket',
            string='Description'),
        'breadcrumb': fields.function(
            _formatted_breadcrumb,
            fnct_search=_search_breadcrumb,
            type='char',
            obj='anytracker.ticket',
            string='Location'),
        'siblings_ids': fields.function(
            _get_siblings,
            type='many2many',
            obj='anytracker.ticket',
            string='Siblings',
            method=True),
        'duration': fields.selection(
            [(0, '< half a day'), (None, 'Will be computed'), (1, 'Half a day')],
            'duration'),
        'child_ids': fields.one2many(
            'anytracker.ticket',
            'parent_id',
            'Sub-tickets',
            required=False),
        'nb_children': fields.function(
            _nb_children,
            method=True,
            string='# of children',
            type='integer',
            store=False, help='Number of children'),
        'participant_ids': fields.many2many(
            'res.users',
            'ticket_assignement_rel',
            'ticket_id',
            'user_id',
            required=False),
        'parent_id': fields.many2one(
            'anytracker.ticket',
            'Parent',
            required=False,
            domain="[('id','child_of',project_id)]",
            ondelete='cascade'),
        'project_id': fields.many2one(
            'anytracker.ticket',
            'Project',
            ondelete='cascade',
            domain=[('parent_id', '=', False)],
            readonly=True),
        'requester_id': fields.many2one(
            'res.users',
            'Requester'),
        #'active': fields.boolean(
        #    'Active',
        #    help=("If the active field is set to False, "
        #          "it will allow you to hide the ticket without removing it.")),

    }

    _defaults = {
        'duration': 0,
        'parent_id': _default_parent_id,
        'project_id': _default_project_id,

    }

    _sql_constraints = [('number_uniq', 'unique(number)', 'Number must be unique!')]
