# coding: utf-8
from openerp import models, fields


class Ticket(models.Model):
    # TODO: We shoudn't have to add fields in this model for that!!
    _inherit = 'anytracker.ticket'

    id_mindmap = fields.Char(
        'ID MindMap',
        size=64)
    created_mindmap = fields.Datetime(
        'Created MindMap')
    modified_mindmap = fields.Datetime(
        'Modified MindMap')
    modified_openerp = fields.Datetime(
        'Modified OpenERP')

    def makeTreeData(self):
        '''Return all ticket of a tree so ordered
        '''
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
            tickets = self.search([('parent_id', '=', ticket_branch['id'])])
            for ticket in tickets:
                if 'child' not in ticket_branch:
                    ticket_branch['child'] = []
                ticket_branch['child'].append(ticket.read(data_to_retrieve)[0])
                makeRecursTree(
                    ticket_branch['child'][len(ticket_branch['child']) - 1])

        ticket_tree = []
        for ticket_tree_data in self.read(data_to_retrieve):
            ticket_tree.append(ticket_tree_data)
            ticket_tree_data = makeRecursTree(ticket_tree_data)
        return ticket_tree
