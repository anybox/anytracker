# coding: utf-8
from osv import fields, osv
from tools.translate import _
import time

class ticket(osv.osv):

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

    def write(self, cr, uid, ids, values, context=None):
        """write the project_id when writing the parent
        """
        if type(ids) is not list: ids = [ids]
        assert(len(ids)==1)
        ticket_id = ids[0]
        if 'parent_id' in values:
            breadcrumb = self._breadcrumb(cr, uid, ids, context)[ticket_id]
            values['project_id'] = breadcrumb[0].id
        return super(ticket, self).write(cr, uid, ids, values, context)

    def create(self, cr, uid, values, context=None):
        """write the project_id when writing the parent
        """
        parent_id = values.get('parent_id')
        if parent_id:
            breadcrumb = self._breadcrumb(cr, uid, [parent_id], context)[parent_id]
            if breadcrumb[0]:
                values['project_id'] = breadcrumb[0].id
        return super(ticket, self).create(cr, uid, values, context)

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
            type='text', 
            obj='anytracker.ticket', 
            string='Description'),
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
        'assignedto_ids': fields.many2many(
            'res.users', 
            'ticket_assignement_rel', 
            'ticket_id', 
            'user_id', 
            required=False),
        'parent_id': fields.many2one(
            'anytracker.ticket', 
            'Parent', 
            required=False, 
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


    def makeTreeData(self, cr, uid, ids, context=None):
        '''Return all ticket of a tree so ordered'''
        DATA_TO_RETRIEVE = ['description', 'modified_mindmap', 'child_ids', 'rating_ids', 'id_mindmap', 'modified_openerp', 'created_mindmap', 'id', 'name']
        def makeRecursTree(ticket_branch):
            ticket_ids = self.search(cr, uid, [('parent_id','=', ticket_branch['id'])])
            for ticket_id in ticket_ids:
                if not ticket_branch.has_key('child'):
                    ticket_branch['child'] = []
                ticket_branch['child'].append(self.read(cr, uid, ticket_id, DATA_TO_RETRIEVE, context))
                makeRecursTree(ticket_branch['child'][len(ticket_branch['child'])-1])
        ticket_tree = []
        for ticket_tree_data in self.read(cr, uid, ids, DATA_TO_RETRIEVE, context):
            ticket_tree.append(ticket_tree_data)
            ticket_tree_data = makeRecursTree(ticket_tree_data)
        return ticket_tree

