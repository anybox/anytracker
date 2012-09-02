# coding: utf-8
from osv import fields, osv
from tools.translate import _

class Ticket(osv.Model):

    _name = 'anytracker.ticket'
    _description = "Anytracker tickets"

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
        """shortened description for the kanban
        """
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            res[ticket.id] = ticket.description and ticket.description[:250] + '...' or False
        return res

    def _breadcrumb(self, cr, uid, ids, context=None):
        """ get all the parents until the root ticket
        """
        res = {}
        for ticket in self.browse(cr, uid, ids, context):
            breadcrumb = []
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
        if not hasattr(ids, '__iter__'): ids = [ids]
        res = super(Ticket, self).write(cr, uid, ids, values, context=context)
        for ticket_id in ids:
            # set the project of the ticket
            self._set_project(cr, uid, ticket_id, context)
        return res

    def create(self, cr, uid, values, context=None):
        """write the project_id when writing the parent
        """
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
        if not ticket.child_ids:
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

    _columns = {
        'name': fields.char('Name', 255, required=True),
        'description': fields.text('Description', required=False),
        'shortened_description': fields.function(
            _shorten_description,
            type='text',
            obj='anytracker.ticket',
            string='Description'),
        'breadcrumb': fields.function(
            _formatted_breadcrumb, 
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
            'Children',
            required=False),
        'nb_children': fields.function(_nb_children,
                            method=True,
                            string='# of children',
                            type='integer',
                            store=False,
                            help='Number of children'),
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
            domain=[('parent_id','=',False)],
            readonly=True),
        'requester_id': fields.many2one(
            'res.users',
            'Requester'),
    }

    _defaults = {
        'duration': 0,
        'parent_id': _default_parent_id,
        'project_id': _default_project_id,
    }


