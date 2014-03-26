# coding: utf-8
from osv import fields, osv


class Ticket(osv.Model):
    _inherit = 'anytracker.ticket'
    _columns = {
        'id_mindmap': fields.char('ID MindMap', size=64),
        'created_mindmap': fields.datetime('Created MindMap'),
        'modified_mindmap': fields.datetime('Modified MindMap'),
        'modified_openerp': fields.datetime('Modified OpenERP'),
    }

    def makeTreeData(self, cr, uid, ids, context=None):
        '''Return all ticket of a tree so ordered'''
        data_to_retrieve = ['description',
                            'modified_mindmap',
                            'child_ids',
                            'rating_ids',
                            'id_mindmap',
                            'modified_openerp',
                            'created_mindmap',
                            'id',
                            'name']

        def makeRecursTree(ticket_branch):
            ticket_ids = self.search(cr, uid, [('parent_id', '=', ticket_branch['id'])])
            for ticket_id in ticket_ids:
                if 'child' not in ticket_branch:
                    ticket_branch['child'] = []
                ticket_branch['child'].append(
                    self.read(cr, uid, ticket_id, data_to_retrieve, context)
                )
                makeRecursTree(ticket_branch['child'][len(ticket_branch['child'])-1])
        ticket_tree = []
        for ticket_tree_data in self.read(cr, uid, ids, data_to_retrieve, context):
            ticket_tree.append(ticket_tree_data)
            ticket_tree_data = makeRecursTree(ticket_tree_data)
        return ticket_tree
