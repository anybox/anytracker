from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class Method(models.Model):
    """ Choice of project method
    such as GTD, anytracker, TMA, etc.
    """
    _name = "anytracker.method"

    code = fields.Char(
        'Name', size=32, help='Short name of the project management method')
    name = fields.Char(
        'Name', size=64, help='Name of the project management method')
    description = fields.Text(
        'Description', help='Description of the method')
    stage_ids = fields.One2many(
        'anytracker.stage', 'method_id', 'Available stages')
    project_id = fields.Many2one(
        'anytracker.ticket', 'Project',
        help='This method is specific to this project. If empty, this is a template method.')

    def customize(self, cr, uid, method_id, context=None):
        """ Create a copy of the method for the project
        """
        project_id = context.get('project_id')
        if not project_id:
            return
        new_meth_id = self.copy(cr, uid, method_id, {'project_id': project_id}, context)
        self.pool.get('anytracker.ticket').write(cr, uid, project_id, {'method_id': new_meth_id})
        return new_meth_id

    def copy(self, cr, uid, method_id, default, context=None):
        method = self.browse(cr, uid, method_id)
        default.update({'name': method.name + ' (specific)'})
        return super(Method, self).copy(cr, uid, method_id, default, context)


class Ticket(models.Model):
    """add method selection on tickets
    """
    _inherit = 'anytracker.ticket'

    def create(self, cr, uid, data, context=None):
        """Set the same method as the parent while creating the ticket
        """
        if 'parent_id' in data and data['parent_id']:
            parent_id = data['parent_id']
            method_id = self.browse(cr, uid, parent_id).method_id.id
            data['method_id'] = method_id
        elif not data.get('method_id'):
            raise except_orm('Error', 'You must choose the method of the project')
        return super(Ticket, self).create(cr, uid, data, context)

    def write(self, cr, uid, ids, values, context=None):
        """Change the method of children when changing the method
        Also try to fix stages, complexities, importances and priorities of subtickets
        """
        stages = self.pool.get('anytracker.stage')
        methods = self.pool.get('anytracker.method')
        ratings = self.pool.get('anytracker.rating')
        priorities = self.pool.get('anytracker.priority')
        importances = self.pool.get('anytracker.importance')
        complexities = self.pool.get('anytracker.complexity')
        old_methods = self.read(cr, uid, ids, ['method_id'], load='_classic_write')
        old_methods = [old_methods] if type(old_methods) is dict else old_methods
        old_methods = dict([(m['id'], m['method_id']) for m in old_methods])
        res = super(Ticket, self).write(cr, uid, ids, values, context)
        # change the method on subtickets as well
        if 'method_id' in values:
            for ticket in self.browse(cr, uid, ids):
                child_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                  ('id', '!=', ticket.id)])
                new_meth_id = values['method_id']
                super(Ticket, self).write(cr, uid, child_ids,
                                          {'method_id': new_meth_id})

                # update subticket to point to the equivalent stage in the new method
                for old_stage in methods.browse(cr, uid, old_methods[ticket.id]).stage_ids:
                    # find children with this stage
                    child_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                      ('stage_id', '=', old_stage.id)])
                    if not child_ids:
                        continue
                    # find a stage with the same code in the new method
                    equ_stage = stages.search(cr, uid, [('state', '=', old_stage.state),
                                                        ('method_id', '=', new_meth_id)])
                    # if no stage found, reset to no stage at all
                    # (should display tickets on the left in the kanban)
                    equ_stage = equ_stage[0] if equ_stage else False
                    cr.execute('update anytracker_ticket set stage_id=%s where id in %s',
                               (equ_stage or None, tuple(child_ids)))

                # update subticket to point to the equivalent priority in the new method
                for old_priority in methods.browse(cr, uid, old_methods[ticket.id]).priority_ids:
                    # find children with this priority
                    child_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                      ('priority_id', '=', old_priority.id)])
                    if not child_ids:
                        continue
                    # find a priority with the same seq in the new method
                    equ_priority = priorities.search(cr, uid, [('seq', '=', old_priority.seq),
                                                               ('method_id', '=', new_meth_id)])
                    # if no priority found, reset to no priority at all
                    # (should display tickets on the left in the kanban)
                    equ_priority = equ_priority[0] if equ_priority else False
                    cr.execute('update anytracker_ticket set priority_id=%s where id in %s',
                               (equ_priority or None, tuple(child_ids)))

                # update subticket to point to the equivalent importance in the new method
                for old_imp in methods.browse(cr, uid, old_methods[ticket.id]).importance_ids:
                    # find children with this importance
                    child_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                      ('importance_id', '=', old_imp.id)])
                    if not child_ids:
                        continue
                    # find a importance with the same code in the new method
                    equ_importance = importances.search(cr, uid, [('seq', '=', old_imp.seq),
                                                                  ('method_id', '=', new_meth_id)])
                    # if no importance found, reset to no importance at all
                    # (should display tickets on the left in the kanban)
                    equ_importance = equ_importance[0] if equ_importance else False
                    cr.execute('update anytracker_ticket set importance_id=%s where id in %s',
                               (equ_importance or None, tuple(child_ids)))

                # update ratings of subtickets to point to the equ complexity in the new method
                for old_complex in methods.browse(cr, uid, old_methods[ticket.id]).complexity_ids:
                    # find ratings with this complexity that are related to children
                    rating_ids = ratings.search(cr, uid, [
                        ('ticket_id', 'in', self.search(cr, uid, [('id', 'child_of', ticket.id)])),
                        ('complexity_id', '=', old_complex.id)])
                    if not rating_ids:
                        continue
                    # find a complexity with the same code in the new method
                    equ_complexity = complexities.search(
                        cr, uid, [('value', '=', old_complex.value),
                                  ('method_id', '=', new_meth_id)])
                    # if no complexity found, reset to no complexity at all
                    # (should display tickets on the left in the kanban)
                    equ_complexity = equ_complexity[0] if equ_complexity else False
                    cr.execute('update anytracker_rating set complexity_id=%s where id in %s',
                               (equ_complexity or None, tuple(rating_ids)))

                # recompute risk and ratings
                self.recompute_subtickets(cr, uid, ticket.id)

        return res

    def set_custom_method(self, cr, uid, ids, context=None):
        """ Copy the method and set a specific method for this project
        """
        methods = self.pool.get('anytracker.method')
        for ticket in self.browse(cr, uid, ids):
            methods.customize(
                cr, uid, ticket.method_id.id, context={'project_id': ticket.project_id.id})
        return

    method_id = fields.Many2one(
        'anytracker.method',
        'Method',
        help='Method of the project',
        ondelete="restrict")
    project_method_id = fields.Many2many(
        'anytracker.method', 'anytracker_method_rel', 'anytracker_id', 'method_id',
        readonly=True,
        string='Method of the project',
        help='Project method')
