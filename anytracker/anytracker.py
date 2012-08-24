# coding: utf-8
from osv import fields, osv
from tools.translate import _

class Ticket(osv.osv):

    _name = 'anytracker.ticket'
    _description = "Tickets for project management"

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

    def _create_menu(self, cr, uid, project, context=None):
        """Create a menu for a project
        """
        xml_pool = self.pool.get('ir.model.data')
        uid = self._get_admin_id(cr, uid, context=context)
        action_id = self.pool.get('ir.actions.act_window').create(cr, uid,
            {'name': project.name,
             'res_model': 'anytracker.ticket',
             'view_mode': 'kanban,tree,page,form',
             'view_id': xml_pool.get_object_reference(cr, uid, 'anytracker', 'tickets_view_kanban')[1],
             'context': {
                'search_default_project_id': project.id,
                'default_project_id': project.id,
                'default_method_id': project.method_id.id},
             # warning: the domain below is also used to find the action at delete time
             'domain': "[('project_id','=',%s),('child_ids','=',False),('stage_id','!=',False)]" % project.id,
            })
        self.pool.get('ir.ui.menu').create(cr, uid,
            {'name': project.name,
             'parent_id': xml_pool.get_object_reference(cr, uid, 'anytracker', 'projects')[1],
             'action': 'ir.actions.act_window,'+str(action_id),
            })

    def _delete_menu(self, cr, uid, project, context=None):
        """delete the menu for a project
        """
        # delete the action
        act_pool = self.pool.get('ir.actions.act_window')
        uid = self._get_admin_id(cr, uid, context=context)
        action_id = act_pool.search(cr, uid,
            [('res_model','=','anytracker.ticket'),
            # warning: the domain below is defined in the _create_menu method
             ('domain','=',"[('project_id','=',%s),('child_ids','=',False),('stage_id','!=',False)]" % project.id)])
        act_pool.unlink(cr, uid, action_id)

        # delete the menu
        menu_pool = self.pool.get('ir.ui.menu')
        menu_id = menu_pool.search(cr, uid,
            [('name','=',project.name),
             ('action','=','ir.actions.act_window,'+str(action_id))])
        menu_pool.unlink(cr, uid, menu_id)

    def _set_project(self, cr, uid, ticket_id, context=None):
        """store the root ticket (the project) in the ticket
        Should be more efficient than looking up the project everytime
        """
        ticket = self.browse(cr, uid, ticket_id, context)
        parent_id = ticket.parent_id and ticket.parent_id.id
        if parent_id:
            breadcrumb = self._breadcrumb(cr, uid, [parent_id], context)[parent_id] + [ticket]
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


            # create a menu for the project
            if 'parent_id' in values and values['parent_id']==False:
                project = self.browse(cr, uid, ticket_id, context)
                self._create_menu(cr, uid, project, context)
            if 'parent_id' in values and values['parent_id']:
                project = self.browse(cr, uid, ticket_id, context)
                self._delete_menu(cr, uid, project, context)

        return res

    def create(self, cr, uid, values, context=None):
        """write the project_id when writing the parent
        """
        ticket_id = super(Ticket, self).create(cr, uid, values, context=context)
        # set the project of the ticket
        self._set_project(cr, uid, ticket_id, context)

        # create a menu for the project
        if not values.get('parent_id'):
            project = self.browse(cr, uid, ticket_id, context)
            self._create_menu(cr, uid, project, context)

        return ticket_id

    def unlink(self, cr, uid, ids, context=None):
        """delete the menu corresponding to the project
        """
        for ticket in self.browse(cr, uid, ids, context):
            if not ticket.parent_id:
                self._delete_menu(cr, uid, ticket, context)

        return super(Ticket, self).unlink(cr, uid, ids, context=context)

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
            ondelete='cascade'), #TODO ondelete doesnt seem to work
        'project_id': fields.many2one(
            'anytracker.ticket',
            'Project',
            ondelete='cascade',
            domain=[('parent_id','=',False)],
            readonly=True),
        'requester_id': fields.many2one(
            'res.users',
            'Requester'),
        'id_mindmap': fields.char(
            'ID MindMap',
            size=64),
        'created_mindmap': fields.datetime('Created MindMap'),
        'modified_mindmap': fields.datetime('Modified MindMap'),
        'modified_openerp': fields.datetime('Modified OpenERP'),
    }

    _defaults = {
        'duration': 0,
    }


