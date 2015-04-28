# coding: utf-8
from openerp.osv import orm
from openerp.osv import fields
from tools.translate import _
from openerp import SUPERUSER_ID


class Stage(orm.Model):
    """Stage of a ticket.
    Correspond to kanban columns
    """
    _name = 'anytracker.stage'
    _order = 'sequence'
    _columns = {
        'name': fields.char('name', size=64, required=True, translate=True),
        'description': fields.text('Description', translate=True),
        'state': fields.char('state', size=64, required=True),
        'method_id': fields.many2one('anytracker.method', 'Project method',
                                     required=True, ondelete='cascade'),
        'sequence': fields.integer('Sequence', help='Sequence'),
        'force_rating': fields.boolean(
            'Force rating', help='Forbid entering this stage without a rating on the ticket'),
        'forbidden_complexity_ids': fields.many2many(
            'anytracker.complexity',
            'anytracker_stage_forbidden_complexities',
            'stage_id', 'complexity_id',
            'Forbidden complexities', help='complexities forbidden for this stage'),
        'progress': fields.float(
            'Progress', help='Progress value of the ticket reaching this stage'),
        'groups_allowed': fields.many2many('res.groups',
                                           'anytracker_stage_res_groups_rel',
                                           'res_group_id',
                                           'anytracker_stage_id',
                                           'Authorized groups to move ticket to this stage'),
    }

    _defaults = {'groups_allowed': False}


class Ticket(orm.Model):
    """ Add stage and progress functionality to tickets
    Progress is based on stages. Each stage has a progress,
    and the progress is copied on the ticket
    """

    _inherit = 'anytracker.ticket'

    def _read_group_stage_ids(self, cr, uid, ids, domain, read_group_order=None,
                              access_rights_uid=None, context=None):
        """return all stage names for the group_by directive, so that the kanban
        has all columns even if there is no ticket in a stage.
        """
        access_rights_uid = access_rights_uid or uid
        # XXX improve the filter to handle categories
        stages = self.pool.get('anytracker.stage')
        tickets = self.pool.get('anytracker.ticket')
        active_id = tickets.browse(cr, uid, context.get('active_id'))
        project_id = active_id.project_id
        if not project_id:
            return [], {}
        method = project_id.method_id
        if not method:
            return [], {}
        stage_ids = stages.search(cr, uid, [('method_id', '=', method.id)], context=context)
        stages_data = stages.read(cr, access_rights_uid, stage_ids,
                                  ['name', 'groups_allowed'], context=context)
        groups = set(self.user_base_groups(cr, uid))
        # we only fold empty and forbidden columns (TODO: replace progress with state)
        folds = {
            s['id']:
            bool(s['groups_allowed']
                 and not groups.intersection(set(s['groups_allowed']))
                 and not tickets.search(cr, uid, [('stage_id', '=', s['id']),
                                                  ('id', 'child_of', active_id.id)]))
            for s in stages_data}
        return [(s['id'], s['name']) for s in stages_data], folds

    def stage_previous(self, cr, uid, ids, context=None):
        """move the ticket to the previous stage
        """
        stages = self.pool.get('anytracker.stage')
        for ticket in self.browse(cr, uid, ids, context):
            method = ticket.project_id.method_id
            if not method:
                raise orm.except_orm(_('Warning !'), _('No method defined in the project.'))
            stage_id = ticket.stage_id.id
            stage_ids = stages.search(cr, uid, [('method_id', '=', method.id)])
            if stage_id == stage_ids[0]:  # first stage
                next_stage = False
            elif stage_id not in stage_ids:  # no stage
                continue
            else:
                next_stage = stage_ids[stage_ids.index(stage_id)-1]
            self.write(cr, uid, [ticket.id], {'stage_id': next_stage}, context)

    def stage_next(self, cr, uid, ids, context=None):
        """move the ticket to the next stage
        """
        stages = self.pool.get('anytracker.stage')
        for ticket in self.browse(cr, uid, ids, context):
            method = ticket.project_id.method_id
            if not method:
                raise orm.except_orm(_('Warning !'), _('No method defined in the project.'))
            stage_id = ticket.stage_id.id
            stage_ids = stages.search(cr, uid, [('method_id', '=', method.id)])
            if stage_id == stage_ids[-1]:  # last stage
                raise orm.except_orm(_('Warning !'), _("You're already in the last stage"))
            elif stage_id not in stage_ids:  # no stage
                next_stage = stage_ids[0]
            else:
                next_stage = stage_ids[stage_ids.index(stage_id)+1]
            self.write(cr, uid, [ticket.id], {'stage_id': next_stage}, context)

    def create(self, cr, uid, values, context=None):
        """select the default stage if parent is selected lately
        """
        if not values.get('stage_id'):
            if values.get('parent_id'):
                method = self.browse(cr, uid, values.get('parent_id')).method_id
            else:
                methods = self.pool.get('anytracker.method')
                method = methods.browse(cr, uid, values['method_id'])
            values['stage_id'] = method.get_first_stage()[method.id]
        stages = self.pool.get('anytracker.stage')
        values['progress'] = (stages.browse(cr, uid, values['stage_id']).progress
                              if values['stage_id'] else 0.0)
        ticket_id = super(Ticket, self).create(cr, uid, values, context)
        # loop up to the root
        ticket = self.browse(cr, uid, ticket_id, context)
        parent = ticket.parent_id
        while parent:
            child_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                              ('type.has_children', '=', False),
                                              ('id', '!=', parent.id)])
            if ticket.id not in child_ids:
                child_ids.append(ticket.id)
            children = len(child_ids)
            new_progress = (parent.progress*(children-1)+(ticket.stage_id.progress or 0))/children
            parent.write({'progress': new_progress})
            parent = parent.parent_id
        return ticket_id

    def unlink(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for ticket_id in ids:
            ticket = self.browse(cr, uid, ticket_id, context)
            parent = ticket.parent_id
            ticket_progress = ticket.progress
            ticket_id = super(Ticket, self).unlink(cr, uid, ids, context)
            while parent:
                child_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                                  ('type.has_children', '=', False),
                                                  ('id', '!=', parent.id)])
                children = len(child_ids)
                if children:
                    new_progress = (parent.progress*(children+1)-ticket_progress)/children
                    parent.write({'progress': new_progress})
                parent = parent.parent_id
            return ticket_id

    def user_base_groups(self, cr, uid):
        """ return the base (not implied) groups of the uid
        """
        cr.execute('select gu.gid from res_groups_users_rel gu, res_users u '
                   'where u.id=gu.uid and u.id=%s '
                   'EXCEPT select gi.hid '
                   'from res_groups_implied_rel gi, res_groups_users_rel gu, res_users u '
                   'where u.id=gu.uid and u.id=%s and gu.gid=gi.gid;', (uid, uid))
        return [i[0] for i in cr.fetchall()]

    def write(self, cr, uid, ids, values, context=None):
        """set permission and children stages when writing stage_id
        """
        # check we can do this
        stage_id = values.get('stage_id')
        if stage_id and uid != SUPERUSER_ID:
            stages = self.pool.get('anytracker.stage')
            stage_groups = set(stages.read(cr, uid, values['stage_id'], ['groups_allowed'],
                                           load='_classic_write')['groups_allowed'])
            user_groups = set(self.user_base_groups(cr, uid))
            if stage_groups and not stage_groups.intersection(user_groups):
                raise orm.except_orm("Operation forbidden",
                                     "You can't move this ticket to this stage")

        # save the previous progress
        if 'stage_id' in values:
            old_progress = {t.id: t.stage_id.progress
                            for t in self.browse(cr, uid, ids, context)}

        res = super(Ticket, self).write(cr, uid, ids, values, context=context)

        # do nothing if we didn't modify the stage
        stage_id = values.get('stage_id', None)
        if not stage_id:
            return res

        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for ticket in self.browse(cr, uid, ids, context):
            # check stage enforcements
            stage = self.pool.get('anytracker.stage').browse(cr, uid, stage_id, context)
            if not ticket.rating_ids and stage.force_rating and not ticket.type.has_children:
                raise orm.except_orm(_('Warning !'),
                                     _('You must rate the ticket "%s" to enter the "%s" stage'
                                       % (ticket.name, stage.name)))
            if ticket.my_rating.id in [i.id for i in (stage.forbidden_complexity_ids or [])]:
                    raise orm.except_orm(
                        _('Warning !'),
                        _('The ticket "%s" is rated "%s" so it cannot enter this stage'
                          % (ticket.name, ticket.my_rating.name)))
            # set all children as well
            super(Ticket, self).write(cr, uid, ticket.id, {'stage_id': stage_id}, context)
            self.write(cr, uid, [i.id for i in ticket.child_ids], {'stage_id': stage_id}, context)

        # Climb the tree from the ticket to the root
        # and recompute the progress of parents
        for ticket in self.browse(cr, uid, ids, context):
            ticket.write({'progress': ticket.stage_id.progress})
            parent = ticket.parent_id
            # loop up to the root
            while parent:
                child_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                                  ('type.has_children', '=', False),
                                                  ('id', '!=', parent.id)])
                if ticket.id not in child_ids:
                    child_ids.append(ticket.id)
                progression = (ticket.stage_id.progress
                               - (old_progress[ticket.id]or 0.0)) / len(child_ids)
                new_progress = parent.progress + progression
                parent.write({'progress': new_progress})
                parent = parent.parent_id
        return res

        return super(Ticket, self).write(cr, uid, ids, values, context=context)

    def _default_stage(self, cr, uid, context):
        active_id = context.get('active_id')
        if not active_id:
            return False
        method = self.browse(cr, uid, context.get('active_id')).method_id
        return method.get_first_stage()[method.id]

    def recompute_progress(self, cr, uid, ids, context=None):
        """recompute the overall progress of the ticket, based on subtickets.
        And recompute sub-nodes as well
        """
        if not context:
            context = {}
        for ticket in self.browse(cr, uid, ids, context):
            if not ticket.type.has_children:
                self.write(cr, uid, ticket.id, {'progress': ticket.stage_id.progress}, context)
            else:
                leaf_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                 ('type.has_children', '=', False),
                                                 ('id', '!=', ticket.id)])
                for leaf in self.browse(cr, uid, leaf_ids, context):
                    leaf.write({'progress': leaf.stage_id.progress})

            sub_node_ids = self.search(cr, uid, [('id', 'child_of', ticket.id),
                                                 ('type.has_children', '=', True),
                                                 ('id', '!=', ticket.id)])
            for node_id in [ticket.id] + sub_node_ids:
                leaf_ids = self.search(cr, uid, [('id', 'child_of', node_id),
                                                 ('type.has_children', '=', False),
                                                 ('id', '!=', node_id)])
                progresses = self.read(cr, uid, leaf_ids, ['progress'])
                nb_tickets = len(progresses)
                if nb_tickets != 0:
                    progress = sum([t['progress'] or 0.0 for t in progresses]) / float(nb_tickets)
                else:
                    progress = ticket.stage_id.progress
                self.write(cr, uid, node_id, {'progress': progress}, context)
        return True

    def _constant_one(self, cr, uid, ids, *a, **kw):
        return {i: 1 for i in ids}

    _columns = {
        'stage_id': fields.many2one(
            'anytracker.stage',
            'Stage',
            select=True,
            domain="[('method_id','=',method_id)]"),
        'progress': fields.float(
            'Progress',
            select=True,
            group_operator="avg"),
        # this field can be used to count tickets if the only available operation
        # on them is to sum field values (shameless hack for charts)
        'constant_one': fields.function(
            _constant_one, type='integer',
            obj='anytracker.ticket',
            string='Constant one',
            store=True,
            invisible=True),
    }

    _group_by_full = {
        'stage_id': _read_group_stage_ids,
    }

    _defaults = {
        'stage_id': _default_stage,
        'progress': 0.0,
    }


class Method(orm.Model):
    _inherit = 'anytracker.method'
    _columns = {
        'stage_ids': fields.one2many(
            'anytracker.stage',
            'method_id',
            'Stages',
            help="The stages associated to this method"),
    }

    def get_first_stage(self, cr, uid, ids, context=None):
        """ Return the id of the first stage of a method"""
        res = {}
        for method in self.browse(cr, uid, ids, context):
            stages = [(s.progress, s.id) for s in method.stage_ids]
            res[method.id] = sorted(stages)[0][1] if len(stages) else False
        return res
