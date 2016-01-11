from openerp import models, fields
from openerp.exceptions import except_orm


class Method(models.Model):
    """ Choice of project method
    such as GTD, anytracker, TMA, etc.
    """
    _name = "anytracker.method"

    code = fields.Char(
        'Name',
        size=32,
        help='Short name of the project management method')
    name = fields.Char(
        'Name',
        size=64,
        help='Name of the project management method')
    description = fields.Text(
        'Description',
        help='Description of the method')
    stage_ids = fields.One2many(
        'anytracker.stage',
        'method_id',
        'Available stages',
        copy=True)
    project_id = fields.Many2one(
        'anytracker.ticket',
        'Project',
        help='This method is specific to this project. '
             'If empty, this is a template method.')

    def customize(self):
        """ Create a copy of the method for the project
        """
        TICKET = self.env['anytracker.ticket']
        project = TICKET.browse(self.env.context.get('project_id'))
        if not project:
            return
        new_method = self.copy({'project_id': project.id})
        project.write({'method_id': new_method.id})
        return new_method

    def copy(self, default):
        default.update({'name': self.name + ' (specific)'})
        return super(Method, self).copy(default)


class Ticket(models.Model):
    """add method selection on tickets
    """
    _inherit = 'anytracker.ticket'

    def create(self, values):
        """Set the same method as the parent while creating the ticket
        """
        parent_id = values.get('parent_id')
        if parent_id:
            values['method_id'] = self.browse(parent_id).method_id.id
        if not values.get('method_id'):
            raise except_orm('Error',
                             'You must choose the method of the project')
        return super(Ticket, self).create(values)

    def write(self, values):
        """Change the method of children when changing the method
        Also try to fix stages, complexities, importances and priorities
        of subtickets
        """
        STAGE = self.env['anytracker.stage']
        RATING = self.env['anytracker.rating']
        PRIORITY = self.env['anytracker.priority']
        IMPORTANCE = self.env['anytracker.importance']
        COMPLEXITY = self.env['anytracker.complexity']
        oldmethods = {t.id: t.method_id for t in self}
        res = super(Ticket, self).write(values)
        # change the method on subtickets as well
        if 'method_id' not in values:
            return res

        for ticket in self:
            children = self.search([('id', 'child_of', ticket.id),
                                    ('id', '!=', ticket.id)])
            new_meth_id = values['method_id']
            super(Ticket, children).write({'method_id': new_meth_id})

            # point subtickets to the equivalent stage in the new method
            for oldstage in oldmethods[ticket.id].stage_ids:
                # find children with this stage
                children = self.search([('id', 'child_of', ticket.id),
                                        ('stage_id', '=', oldstage.id)])
                if not children:
                    continue
                # find a stage with the same code in the new method
                equ_stage = STAGE.search([('state', '=', oldstage.state),
                                          ('method_id', '=', new_meth_id)])
                # if no stage found, reset to no stage at all
                # (should display tickets on the left in the kanban)
                equ_stage = equ_stage[0].id if equ_stage else False
                self.env.cr.execute(
                    'update anytracker_ticket '
                    'set stage_id=%s where id in %s',
                    (equ_stage or None, tuple(children.ids)))

            # point subtickets to the equivalent priority in the new method
            for oldprio in oldmethods[ticket.id].priority_ids:
                # find children with this priority
                children = self.search([('id', 'child_of', ticket.id),
                                        ('priority_id', '=', oldprio.id)])
                if not children:
                    continue
                # find a priority with the same seq in the new method
                equ_prio = PRIORITY.search([('seq', '=', oldprio.seq),
                                            ('method_id', '=', new_meth_id)])
                # if no priority found, reset to no priority at all
                # (should display tickets on the left in the kanban)
                equ_prio = equ_prio[0].id if equ_prio else False
                self.env.cr.execute('update anytracker_ticket '
                                    'set priority_id=%s where id in %s',
                                    (equ_prio or None, tuple(children.ids)))

            # point subtickets to the equivalent importance in the new method
            for oldimp in oldmethods[ticket.id].importance_ids:
                # find children with this importance
                children = self.search([('id', 'child_of', ticket.id),
                                        ('importance_id', '=', oldimp.id)])
                if not children:
                    continue
                # find a importance with the same code in the new method
                equ_imp = IMPORTANCE.search([('seq', '=', oldimp.seq),
                                             ('method_id', '=', new_meth_id)])
                # if no importance found, reset to no importance at all
                # (should display tickets on the left in the kanban)
                equ_imp = equ_imp[0].id if equ_imp else False
                self.env.cr.execute(
                    'update anytracker_ticket set importance_id=%s'
                    ' where id in %s',
                    (equ_imp or None, tuple(children.ids)))

            # point subtickets to the equiv complexity in the new method
            for oldcplx in oldmethods[ticket.id].complexity_ids:
                # find ratings with this complexity and related to children
                ratings = RATING.search([
                    ('ticket_id', 'in',
                     self.search([('id', 'child_of', ticket.id)]).ids),
                    ('complexity_id', '=', oldcplx.id)])
                if not ratings:
                    continue
                # find a complexity with the same code in the new method
                equ_cmplx = COMPLEXITY.search(
                    [('value', '=', oldcplx.value),
                     ('method_id', '=', new_meth_id)])
                # if no complexity found, reset to no complexity at all
                # (should display tickets on the left in the kanban)
                equ_cmplx = equ_cmplx[0].id if equ_cmplx else False
                self.env.cr.execute(
                    'update anytracker_rating set complexity_id=%s '
                    'where id in %s',
                    (equ_cmplx or None, tuple(ratings.ids)))

            # recompute risk and ratings
            ticket.recompute_subtickets()

        return res

    def set_custom_method(self):
        """ Copy the method and set a specific method for this project
        """
        for ticket in self:
            ticket.method_id.with_context(
                {'project_id': ticket.project_id.id}).customize()
        return

    method_id = fields.Many2one(
        'anytracker.method',
        'Method',
        help='Method of the project',
        ondelete="restrict")
    project_method_id = fields.Many2many(
        'anytracker.method',
        'anytracker_method_rel',
        'anytracker_id',
        'method_id',
        readonly=True,
        string='Method of the project',
        help='Project method')
