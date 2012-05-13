from osv import fields, osv
from tools.translate import _
import time



class workflow1(osv.osv):

    _name = 'anytracker.ticket.workflow1'

    _columns = {
        'name': fields.char('name', size=64, required=True),
        'state': fields.char('state', size=64, required=True),
        'default': fields.boolean('Default'),
    }

    _defaults = {
         'default': lambda *a: False,
    }


class anytracker_ticket_history(osv.osv):

    _name = 'anytracker.ticket.history'
    _description = 'History of ticket'

    _columns = {
        'create_uid': fields.many2one('res.users', 'User', readonly=True),
        'create_date': fields.datetime('Create Date', readonly=True),
        'modification': fields.text('Modification', readonly=True),
    }


class ticket(osv.osv):

    _name = 'anytracker.ticket'
    _description = "Tickets for project management"

    def _get_siblings(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for t in self.browse(cr, uid, ids, context):
            domain = [
                ('parent_id', '=', t.parent_id.id),  # the same parent
                ('id', '!=', t.id),  # not me
            ]
            res[t.id] = self.search(cr, uid, domain, context=context)
        return res

    _columns = {
        'name': fields.char('Name', 255, required=True),
        'description': fields.text('Description', required=False),
        'state': fields.char('state', 30, required=False),
        'siblings_ids': fields.function(_get_siblings, type='many2many', obj='anytracker.ticket', string='Siblings', method=True),
        'duration': fields.selection([(0, '< half a day'), (None, 'Will be computed'), (1, 'Half a day')], 'duration'),
        'child_ids': fields.one2many('anytracker.ticket', 'parent_id', 'Children', required=False),
        'assignedto_ids': fields.many2many('res.users', 'ticket_assignement_rel', 'ticket_id', 'user_id', required=False),
        'parent_id': fields.many2one('anytracker.ticket', 'Parent', required=False),
        'requester_id': fields.many2one('res.users', 'Requester'),
        'workflow_id': fields.many2one('anytracker.ticket.workflow1', 'kanban_status', required=True),
        'history_ids': fields.many2many('anytracker.ticket.history', 'ticket_ticket_history_rel', 'ticket_id', 'history_id', 'History'),
        'id_mindmap': fields.char('ID MindMap', size=64),
        'created_mindmap': fields.datetime('Created MindMap'),
        'modified_mindmap': fields.datetime('Modified MindMap'),
        'modified_openerp': fields.datetime('Modified OpenERP'),
    }

    _defaults = {
        'state': 'Analyse',
        'duration': 0,
    }

    def _add_history(self, cr, uid, values, context=None):
        if not context: context = {}
        vals = ""
        if context.get('import_mindmap', False):
            vals += _("Update from Import MindMap\n")
        def _all2many(name, obj, val):
            if not val:
                return ""
            vals = _('Modify field %s\n') % name
            obj = self.pool.get(obj)
            for i in val:
                vals += " => "
                if i[0] == 0:
                    vals += _('Create new value %s') % i[2].get('name')
                elif i[0] == 1:
                    iname = i[2].get('name')
                    if not iname:
                        iname= obj.name_get(cr, uid, [i[1]], context=context)[0][1]
                    vals += _('Modify value %s') % iname
                elif i[0] == 2:
                    iname= obj.name_get(cr, uid, [i[1]], context=context)[0][1]
                    vals += _('Remove value %s') % iname
                elif i[0] == 3:
                    iname= obj.name_get(cr, uid, [i[1]], context=context)[0][1]
                    vals += _('Unlink value %s') % iname
                elif i[0] == 4:
                    iname= obj.name_get(cr, uid, [i[1]], context=context)[0][1]
                    vals += _('Link value %s') % iname
                elif i[0] == 5:
                    iname= obj.name_get(cr, uid, [i[1]], context=context)[0][1]
                    vals += _('Unlink all value %s') % iname
                elif i[0] == 6:
                    iname= obj.name_get(cr, uid, i[1], context=context)
                    vals += _('Unlink all value  and add:') % iname
                    for y, z in iname:
                        vals += '\n   * ' + z

                vals += '\n'

            return vals

        def _many2one(fieldname, obj, val):
            if not val:
                return ""
            obj = self.pool.get(obj)
            nameget = obj.name_get(cr, uid, [val], context=context)[0][1]
            return _('Modify field %s with new valeur %s\n') % (fieldname, nameget)

        for k, v in values.items():
            if k == 'workflow_id':
                vals += _many2one(k, 'anytracker.ticket.workflow1', v)
            elif k == 'history_ids':
                continue
            elif k == 'parent_id':
                vals += _many2one(k, 'anytracker.ticket', v)
            elif k == 'requester_id':
                vals += _many2one(k, 'res.users', v)
            elif k == 'assignedto_ids':
                vals += _all2many(k, 'res.users', v)
            elif k == 'child_ids':
                vals += _all2many(k, 'anytracker.ticket', v)
            elif k == 'duration':
                col = dict(self._columns[k].selection)
                vals += _('Modify field %s with new valeur %s\n') % (k, col.get(v))
            else:
                vals += _('Modify field %s with new valeur %s\n') % (k, v)


        values['history_ids'] = [(0, 0, {'modification': vals})]
        return values

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

    def create(self, cr, uid, values, context=None):
        if values.get('id_mindmap'):
            # Create by import
            values['modified_openerp'] = values.get('modified_mindmap')
        else:
            #TODO generate id_mindmap
            #TODO generate time
            pass
        values = self._add_history(cr, uid, values, context=context)
        return super(ticket, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        if not context: context = {}
        def _be_updated():
            for i in ('name', 'description', 'rating_ids', 'workflow_id', 'parent_id'):
                if values.get(i):
                    return True
            return False
        if values.get('modified_mindmap'):
            for i in self.read(cr, uid, ids, ['name', 'modified_openerp'], context=context):
                if values['modified_mindmap'] < i['modified_openerp']:
                    raise osv.except_osv(_('Error'), _('You can t update the ticket %s') % i['name'])
        elif context.get('import_mindmap', False):
            # description and complexity
            pass #TODO
        elif _be_updated():
            values['modified_openerp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        values = self._add_history(cr, uid, values, context=context)
        return super(ticket, self).write(cr, uid, ids, values, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
