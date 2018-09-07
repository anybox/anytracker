# coding: utf-8
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp import SUPERUSER_ID


class Stage(models.Model):
    """Stage of a ticket.
    Correspond to kanban columns
    """
    _name = 'anytracker.stage'
    _order = 'sequence'

    name = fields.Char(
        'name',
        size=64,
        required=True,
        translate=True)
    description = fields.Text(
        'Description',
        translate=True)
    state = fields.Char(
        'state',
        size=64,
        required=True)
    method_id = fields.Many2one(
        'anytracker.method',
        'Project method',
        required=True,
        ondelete='cascade')
    sequence = fields.Integer(
        'Sequence',
        help='Sequence')
    force_rating = fields.Boolean(
        'Force rating',
        help='Forbid entering this stage without a rating on the ticket')
    forbidden_complexity_ids = fields.Many2many(
        'anytracker.complexity',
        'anytracker_stage_forbidden_complexities',
        'stage_id',
        'complexity_id',
        'Forbidden complexities',
        help='complexities forbidden for this stage')
    progress = fields.Float(
        'Progress',
        help='Progress value of the ticket reaching this stage')
    groups_allowed = fields.Many2many(
        'res.groups',
        'anytracker_stage_res_groups_rel',
        'res_group_id',
        'anytracker_stage_id',
        'Authorized groups to move ticket to this stage',
        default=False)


class Ticket(models.Model):
    """ Add stage and progress functionality to tickets
    Progress is based on stages. Each stage has a progress,
    and the progress is copied on the ticket
    """

    _inherit = 'anytracker.ticket'

    @api.multi
    def _read_group_stage_ids(self, domain, read_group_order=None,
                              access_rights_uid=None, context=None):
        """return all stage names for the group_by directive, so that the kanban
        has all columns even if there is no ticket in a stage.
        """
        access_rights_uid = access_rights_uid or self.env.uid
        # XXX improve the filter to handle categories
        STAGE = self.env['anytracker.stage']
        TICKET = self.env['anytracker.ticket']
        ticket = TICKET.browse(self.env.context.get('active_id'))
        if not ticket.project_id:
            return [], {}
        method = ticket.project_id.method_id
        if not method:
            return [], {}
        stages = STAGE.search([('method_id', '=', method.id)])
        groups = set(self.user_base_groups())
        # we only fold empty and forbidden columns
        # (TODO: replace progress with state)
        folds = {
            s.id:
                bool(s.groups_allowed
                     and not groups.intersection(set(s.groups_allowed.ids))
                     and not TICKET.search([('stage_id', '=', s.id),
                                            ('id', 'child_of', ticket.id)]))
            for s in stages}
        return [(s.id, s.name) for s in stages], folds

    @api.multi
    def stage_previous(self):
        """move the ticket to the previous stage
        """
        STAGE = self.env['anytracker.stage']
        for ticket in self:
            method = ticket.project_id.method_id
            if not method:
                raise except_orm(_('Warning !'),
                                 _('No method defined in the project.'))
            stages = STAGE.search([('method_id', '=', method.id)])
            stage = ticket.stage_id
            if stage == stages[0]:  # first stage
                next_stage = False
            elif stage not in stages:  # no stage
                continue
            else:
                next_stage = stages[list(stages).index(stage) - 1]
            ticket.write({'stage_id': next_stage.id})

    @api.multi
    def stage_next(self):
        """move the ticket to the next stage
        """
        STAGE = self.env['anytracker.stage']
        for ticket in self:
            method = ticket.project_id.method_id
            if not method:
                raise except_orm(_('Warning !'),
                                 _('No method defined in the project.'))
            stage = ticket.stage_id
            stages = STAGE.search([('method_id', '=', method.id)])
            if stage == stages[-1]:  # last stage
                raise except_orm(_('Warning !'),
                                 _("You're already in the last stage"))
            elif stage not in stages:  # no stage
                next_stage = stages[0]
            else:
                next_stage = stages[list(stages).index(stage) + 1]
            ticket.write({'stage_id': next_stage.id})

    def create(self, values):
        """select the default stage if parent is selected lately
        """
        if not values.get('stage_id'):
            if values.get('parent_id'):
                method = self.browse(values.get('parent_id')).method_id
            else:
                METHOD = self.env['anytracker.method']
                method = METHOD.browse(values['method_id'])
            values['stage_id'] = method.get_first_stage()
        STAGE = self.env['anytracker.stage']
        values['progress'] = (STAGE.browse(values['stage_id']).progress
                              if values['stage_id'] else 0.0)
        ticket = super(Ticket, self).create(values)
        # loop up to the root
        parent = ticket.parent_id
        while parent:
            child_ids = self.search([('id', 'child_of', parent.id),
                                     ('type.has_children', '=', False),
                                     ('id', '!=', parent.id)])
            if ticket not in child_ids:
                child_ids += ticket
            children = len(child_ids)
            new_progress = (parent.progress * (children - 1)
                            + (ticket.stage_id.progress or 0)) / children
            parent.write({'progress': new_progress})
            parent = parent.parent_id
        return ticket

    def unlink(self):
        parent = self.parent_id
        ticket_progress = self.progress
        super(Ticket, self).unlink()
        while parent:
            children = len(self.search([('id', 'child_of', parent.id),
                                        ('type.has_children', '=', False),
                                        ('id', '!=', parent.id)]))
            if children:
                new_progress = (parent.progress * (children + 1)
                                - ticket_progress) / children
                parent.write({'progress': new_progress})
            parent = parent.parent_id
        return True

    def user_base_groups(self):
        """ return the base (not implied) groups of the uid
        """
        cr, uid = self.env.cr, self.env.uid
        cr.execute(
            'SELECT gu.gid from res_groups_users_rel gu, res_users u '
            'WHERE u.id=gu.uid and u.id=%s '
            'EXCEPT select gi.hid '
            'FROM res_groups_implied_rel gi,'
            ' res_groups_users_rel gu, res_users u '
            'WHERE u.id=gu.uid and u.id=%s and gu.gid=gi.gid;', (uid, uid))
        return [i[0] for i in cr.fetchall()]

    def write(self, values):
        """set permission and children stages when writing stage_id
        """
        # check we can do this
        stage_id = values.get('stage_id')
        if stage_id and self.env.user.id != SUPERUSER_ID:
            STAGE = self.env['anytracker.stage']
            stage_groups = set(STAGE.browse(stage_id).groups_allowed.ids)
            user_groups = set(self.user_base_groups())
            if stage_groups and not stage_groups.intersection(user_groups):
                raise except_orm("Operation forbidden",
                                 "You can't move this ticket to this stage")

        # save the previous progress
        if 'stage_id' in values:
            old_progress = {t.id: t.stage_id.progress for t in self}

        res = super(Ticket, self).write(values)

        # do nothing if we didn't modify the stage
        stage_id = values.get('stage_id', None)
        if not stage_id:
            return res

        for ticket in self:
            # check stage enforcements
            stage = self.env['anytracker.stage'].browse(stage_id)
            if (not ticket.rating_ids
                    and stage.force_rating
                    and not ticket.type.has_children):
                raise except_orm(_('Warning !'),
                                 _("You must rate the ticket '%s'"
                                   " to enter the '%s' stage")
                                 % (ticket.name, stage.name))
            if ticket.my_rating in (stage.forbidden_complexity_ids or []):
                raise except_orm(
                    _('Warning !'),
                    _("The ticket '%s' is rated '%s': "
                      "it cannot enter this stage"
                      % (ticket.name, ticket.my_rating.name)))
            # set all children as well
            super(Ticket, ticket).write({'stage_id': stage_id})
            ticket.child_ids.write({'stage_id': stage_id})

        # Climb the tree from the ticket to the root
        # and recompute the progress of parents
        for ticket in self:
            ticket.write({'progress': ticket.stage_id.progress})
            parent = ticket.parent_id
            # loop up to the root
            while parent:
                children = self.search([('id', 'child_of', parent.id),
                                        ('type.has_children', '=', False),
                                        ('id', '!=', parent.id)])
                if ticket not in children:
                    children += ticket
                progression = (ticket.stage_id.progress
                               - (old_progress[ticket.id] or 0.0)
                               ) / len(children)
                new_progress = parent.progress + progression
                parent.write({'progress': new_progress})
                parent = parent.parent_id
        return res

        return super(Ticket, self).write(values)

    def _default_stage(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return False
        method = self.browse(active_id).method_id
        return method.get_first_stage()

    def recompute_progress(self):
        """recompute the overall progress of the ticket, based on subtickets.
        And recompute sub-nodes as well
        """
        for ticket in self:
            if not ticket.type.has_children:
                ticket.write({'progress': ticket.stage_id.progress})
            else:
                leafs = self.search([('id', 'child_of', ticket.id),
                                     ('type.has_children', '=', False),
                                     ('id', '!=', ticket.id)])
                for leaf in leafs:
                    leaf.write({'progress': leaf.stage_id.progress})

            subnodes = self.search([('id', 'child_of', ticket.id),
                                    ('type.has_children', '=', True),
                                    ('id', '!=', ticket.id)])
            for node in [ticket.id] + subnodes:
                leafs = self.search([('id', 'child_of', node.id),
                                     ('type.has_children', '=', False),
                                     ('id', '!=', node.id)])
                progresses = leafs.read(['progress'])
                nb_tickets = len(progresses)
                if nb_tickets != 0:
                    progress = sum([t['progress'] or 0.0 for t in progresses]
                                   ) / float(nb_tickets)
                else:
                    progress = ticket.stage_id.progress
                node.write({'progress': progress})
        return True

    def _constant_one(self):
        for ticket in self:
            ticket.constant_one = 1

    stage_id = fields.Many2one(
        'anytracker.stage',
        string='Stage',
        track_visibility='onchange',
        default=_default_stage,
        index=True,
        domain="[('method_id','=',method_id)]")
    progress = fields.Float(
        string='Progress',
        default=0.0,
        track_visibility='onchange',
        index=True,
        group_operator="avg")
    # this field can be used to count tickets if the only available operation
    # on them is to sum field values (shameless hack for charts)
    # TODO: check if still needed
    constant_one = fields.Integer(compute='_constant_one',
                                  obj='anytracker.ticket',
                                  string='Constant one',
                                  store=True,
                                  invisible=True)

    _group_by_full = {
        'stage_id': _read_group_stage_ids,
    }


class Method(models.Model):
    _inherit = 'anytracker.method'

    stage_ids = fields.One2many(
        'anytracker.stage',
        'method_id',
        'Stages',
        copy=True,
        help="The stages associated to this method")

    def get_first_stage(self):
        """ Return the id of the first stage of a method"""
        if len(self) == 0:
            return False
        stages = [(s.progress, s.id) for s in self.stage_ids]
        return sorted(stages)[0][1] if len(stages) else False
