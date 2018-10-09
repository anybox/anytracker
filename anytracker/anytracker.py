import re
import logging
from lxml import html
from lxml import etree
from collections import defaultdict

from odoo.osv import orm
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__file__)

ticket_regex = re.compile('([Tt]icket ?#?)([\d]+)')


def add_permalinks(dbname, string):
    # replace ticket numbers with permalinks
    if not string:
        return string
    return ticket_regex.subn(
        '<a href="/anytracker/%s/ticket/\\2">\\1\\2</a>' % dbname,
        string)[0]


class Type(models.Model):
    """ Ticket type (project, ticket, deliverable, etc.)
    """
    _name = 'anytracker.ticket.type'

    name = fields.Char(
        'Title',
        size=255,
        required=True)
    code = fields.Char(
        'Code',
        size=255,
        required=True)
    description = fields.Text(
        'Description')
    has_children = fields.Boolean(
        'Can have children')
    default = fields.Boolean(
        'Default for new tickets')
    icon = fields.Binary(
        'Icon in the kanban')


class Ticket(models.Model):
    _name = 'anytracker.ticket'
    _description = "Anytracker tickets"
    _rec_name = 'breadcrumb'
    _order = 'priority DESC, importance DESC, sequence ASC, create_date DESC'
    _parent_store = True
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _has_attachment(self):
        """ check if tickets have attachment(s) or not"""
        ATTACHMENT = self.env['ir.attachment']
        for ticket in self:
            attachments = ATTACHMENT.search([
                ('res_id', '=', ticket.id),
                ('res_model', '=', 'anytracker.ticket')])
            if not attachments:
                ticket.has_attachment = False
            ticket.has_attachment = True

    @api.depends('description')
    def _shortened_description(self):
        """shortened description used in the list view and kanban view
        """
        limit = 150
        for ticket in self:
            d = html.fromstring((ticket.description or '').strip()
                                or '&nbsp;').text_content()
            ticket.shortened_description = (d[:limit] + u'(…)'
                                            if len(d) > limit else d)

    @api.multi
    def get_breadcrumb(self, under_node_id=0):
        """ get all the parents up to the root ticket

        :params under_node_id:
            if supplied, only the part of the breadcrumbs strictly under
            this node will be returned.
        """
        cr = self.env.cr
        sql = ("WITH RECURSIVE parent(id, parent_id, requested_id, name) "
               "AS (SELECT 0, id, id, text('') "
               "    FROM anytracker_ticket t WHERE t.id in %s "
               "    UNION "
               "    SELECT t.id, t.parent_id, p.requested_id, t.name "
               "    FROM parent p, anytracker_ticket t "
               "    WHERE t.id = p.parent_id AND t.id != %s) "
               "SELECT requested_id, id, parent_id, name "
               "    FROM parent WHERE id != 0")
        cr.execute(sql, (tuple(self.ids), under_node_id))
        raw = defaultdict(list)
        for f in cr.fetchall():
            raw[f[0]].append(f[1:])
        return {tid: [dict(zip(('id', 'parent_id', 'name'), line))
                      for line in reversed(t_lines)]
                for tid, t_lines in raw.items()}

    def _formatted_breadcrumb(self):
        """ format the breadcrumb
        TODO : format in the view (in js)
        """
        breadcrumbs = self.get_breadcrumb()
        for ticket in self:
            if ticket.id not in breadcrumbs:
                logger.info(u"Ticket (%s) not in breadcrumbs" % (ticket.id))
                continue
            ticket.breadcrumb = u' / '.join(
                [b['name'] for b in breadcrumbs[ticket.id]])

    def _formatted_rparent_breadcrumb(self):
        """A formatted breadcrumbs of parent, relative to context:active_id

        :returns:
            False for each id if ``active_id`` could not be read from context.
        """
        active_id = self.env.context.get('active_id')
        if active_id is None:
            return
        breadcrumbs = self.get_breadcrumb(under_node_id=active_id)
        for ticket in self:
            if ticket.id in breadcrumbs:
                breadcrumb = breadcrumbs[ticket.id]
                ticket.relative_parent_breadcrumbs = u' / '.join(
                    b['name'] for b in breadcrumb[:-1])
            else:
                ticket.relative_parent_breadcrumbs = u'(breadcrumb ERROR please report!)'

    def _get_root(self):
        """Return the real root ticket (not the project_id of the ticket)
        """
        if not self:
            return False
        if self.parent_id:
            breadcrumb = self.parent_id.get_breadcrumb()
            if not breadcrumb:
                breadcrumb = [self.parent_id.read(['name', 'parent_id'])]
            project_id = breadcrumb[self.parent_id.id][0]['id']
        else:
            # if no parent, we are the project
            project_id = self.id
        return self.browse(project_id)

    def write(self, values):
        """write the project_id when writing the parent.
        Also propagate the (in)active flag to the children
        """
        TYPE = self.env['anytracker.ticket.type']
        children = None
        if 'parent_id' in values:
            root_id = self.browse(values['parent_id'])._get_root().id
            values['project_id'] = root_id
            for ticket in self:
                if ticket.id == values['parent_id']:
                    raise UserError(
                        _(u"Think of yourself. Can you be your own parent?"))
                # if reparenting to False,
                # propagate the current ticket as project for children
                project_id = root_id or ticket.id
                # set the project_id of me and all the children
                children = self.search([('id', 'child_of', ticket.id)])
                super(Ticket, children).write({'project_id': project_id})
                self.browse(values['parent_id']).recompute_subtickets()
        if 'active' in values:
            for ticket in self:
                children = self.search([
                    ('id', 'child_of', ticket.id),
                    ('active', '=', not values['active'])])
                super(Ticket, children).write({'active': values['active']})

        if 'participant_ids' in values:
            if len(self) > 1:
                raise UserError(
                    _('You can modify participants for 1 ticket at a time'))
            participant_ids = set(self.participant_ids.ids)
        # replace ticket numbers with permalinks
        if 'description' in values:
            values['description'] = add_permalinks(
                self.env.cr.dbname, values['description'])

        # don't allow to set a node as ticket if it has children
        if values.get('type'):
            type_id = values['type']
            for ticket in self:
                if ticket.child_ids and not TYPE.browse(type_id).has_children:
                    del values['type']

        res = super(Ticket, self).write(values)
        if 'parent_id' in values:
            for ticket in self:
                method_id = (ticket.parent_id.method_id.id
                             if values['parent_id'] is not False
                             else ticket.method_id.id)
                super(Ticket, children).write({'method_id': method_id})
        # correct the parent to be a node
        if 'parent_id' in values:
            types = TYPE.search([('code', '=', 'node')])
            if types:
                self.browse(values['parent_id']).write({'type': types[0].id})

        if 'participant_ids' in values:
            # subscribe new participants, unsubscribe old ones
            new_p_ids = set(self.participant_ids.ids)
            added_users = new_p_ids - participant_ids
            removed_users = participant_ids - new_p_ids
            self.message_unsubscribe_users(removed_users)
            self.message_subscribe_users(added_users)

            # Needed for the ir_rule,
            # because it involves an sql request for _search_allowed_partners
            # self.env.invalidate_all()  #11373 depreciated in v11 api
            for env in self.env.__class__.envs:
                env.clear()

        return res

    def _get_permalink(self):
        dbname = self.env.cr.dbname
        for ticket in self:
            base_uri = '/anytracker/%s/ticket/' % dbname
            ticket.permalink = base_uri + str(ticket.number)

    @api.model
    def create(self, values):
        """write the project_id when creating
        """
        TYPE = self.env['anytracker.ticket.type']
        SEQUENCE = self.env['ir.sequence']
        types = TYPE.search([('code', '=', 'node')])
        values.update({
            'number': SEQUENCE.sudo().next_by_code('anytracker.ticket')})
        if values.get('parent_id'):
            values['project_id'] = self.browse(
                values['parent_id']).project_id.id

        # project creation: auto-assign the 'node' type
        if not values.get('parent_id') and types:
            values['type'] = types[0].id

        # add myself to the project at creation
        if not values.get('parent_id'):
            p_ids = values.get('participant_ids', [(6, 0, [])])
            if self.env.uid not in p_ids:
                values['participant_ids'] = [
                    (6, 0, [self.env.uid] + p_ids[0][2])]

        # replace ticket numbers with permalinks
        if 'description' in values:
            values['description'] = add_permalinks(
                self.env.cr.dbname, values['description'])

        ticket = super(Ticket, self).create(values)

        if not values.get('parent_id'):
            ticket.write({'project_id': ticket.id})

        # turn the parent into a node
        if 'parent_id' in values and values['parent_id'] and types:
            ticket.browse(values['parent_id']).write({'type': types[0].id})

        # subscribe the followers of the parent,
        # or the participants if this is a project
        # This allows to subscribe or unsubscribe to ticket subtrees
        if ticket.project_id.participant_ids:
            if ticket.parent_id:
                #11375: FIX message_subscribe purpose is to add partners vs users
                #ticket.message_subscribe(ticket.parent_id.message_follower_ids.ids)
                ticket.message_subscribe(
                    partner_ids=ticket.parent_id.message_follower_ids.mapped('partner_id').ids
                )
            else:
                ticket.message_subscribe_users(
                    ticket.participant_ids.ids)

        return ticket

    def _default_parent_id(self):
        """When creating a ticket, return the current ticket as default parent
        or its parent if this is a leaf (to create a sibling)
        """
        active_id = self.env.context.get('active_id')
        if not active_id:
            return False
        ticket = self.browse(active_id)
        if not ticket.parent_id:
            return active_id
        elif not ticket.type.has_children:
            return ticket.parent_id.id
        else:
            return active_id

    def _default_type(self):
        TYPE = self.env['anytracker.ticket.type']
        types = TYPE.search([('default', '=', True)])
        if not types:
            return False
        return types[0]

    def _subnode_ids(self):
        """Return the list of children that are themselves nodes."""
        for ticket in self:
            ticket.subnode_ids = self.search([
                ('parent_id', '=', ticket.id),
                ('type.has_children', '=', True)])

    def _has_subnode(self):
        """Has children that are themselves nodes ?"""
        for ticket in self:
            ticket.has_subnode = self.search(
                [
                    ('parent_id', '=', ticket.id),
                    ('type.has_children', '=', True),
                ],
                count=True
            ) > 0

    def _nb_children(self):
        for ticket in self:
            nb_children = ticket.search([
                ('id', 'child_of', ticket.id)], count=True)
            ticket.nb_children = nb_children

    def _search_breadcrumb(self, operator, value):
        """Use the 'name' in the search function for the parent,
        instead of 'breadcrum' which is implicitly used because of _rec_name
        """
        return [('name', operator, value)]

    @api.multi
    @api.onchange('parent_id')
    def onchange_parent(self):
        """ Fill the method when changing parent
        """
        if not self.parent_id:
            return {}
        self.method_id = self.parent_id.method_id.id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Allow managers to set an empy parent_id (a project)
        """
        fvg = super(Ticket, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and fvg['type'] == 'form':
            ACCESS = self.env['ir.model.access']
            allow = (ACCESS.check_groups('anytracker.group_member')
                     or ACCESS.check_groups('anytracker.group_manager'))
            doc = etree.fromstring(fvg['arch'])
            try:
                node = doc.xpath("//field[@name='parent_id']")[0]
            except Exception:
                logger.error("It seems you're using a broken version of Odoo")
                return fvg
            orm.transfer_modifiers_to_node({'required': not allow}, node)
            fvg['arch'] = etree.tostring(doc)
        return fvg

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
            Overwrite the name_search function to search a ticket
            with their name or thier number
        """
        if not self.env.context.get('legacy_name_search', False):
            args = args or []
            if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
                if name.isdigit():
                    number = int(name)
                    tickets = self.search([('number', '=', number)] + args,
                                          limit=limit)
                else:
                    tickets = self.search([('name', operator, name)] + args,
                                          limit=limit)
                if len(tickets) > 0:
                    return tickets.name_get()

        return super(Ticket, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.multi
    def trash(self):
        """ Trash the ticket
        set active = False, and move to the last stage
        """
        self.write({
            'active': False,
            'state': 'trashed',
            'progress': 100.0,
            'stage_id': False})
        self.recompute_parents()

    @api.multi
    def reactivate(self):
        """ reactivate a trashed ticket
        """
        self.write({'active': True, 'state': 'running'})
        STAGE = self.env['anytracker.stage']
        for ticket in self:
            starts = STAGE.search([('method_id', '=', ticket.method_id.id),
                                   ('progress', '=', 0)])
            if len(starts) != 1:
                raise ValidationError(
                    _('Configuration error ! \n One and only one stage should'
                      'have a 0% progress'))
            # write stage in a separate line to recompute progress & risk
            ticket.write({'stage_id': starts[0].id})
        self.recompute_parents()

    def cron(self):
        """Anytracker CRON tasks
        To be overloaded by submodules
        """
        return

    @api.multi
    def message_subscribe_users(self, user_ids=None, subtype_ids=None):
        if self._name == 'anytracker.ticket':
            for ticket in self:
                children = self.search([('id', 'child_of', ticket.id)])
                super(Ticket, children).message_subscribe_users(
                    user_ids, subtype_ids)
        else:
            super(Ticket, self).message_subscribe_users(user_ids, subtype_ids)

    @api.multi
    def message_unsubscribe_users(self, user_ids=None):
        if self._name == 'anytracker.ticket':
            for ticket in self:
                children = self.search([('id', 'child_of', ticket.id)])
                super(Ticket, children).message_unsubscribe_users(user_ids)
        else:
            super(Ticket, self).message_unsubscribe_users(user_ids)

    @api.depends('participant_ids')
    def _is_participant(self):
        uid = self.env.uid
        for ticket in self:
            ticket.is_participant = uid in ticket.participant_ids.ids

    @api.multi
    def join_project(self):
        for ticket in self:
            if ticket.parent_id:
                continue
            ticket.write({'participant_ids': [(4, self.env.uid)]})

    @api.multi
    def leave_project(self):
        for ticket in self:
            if ticket.parent_id:
                continue
            ticket.write({'participant_ids': [(3, self.env.uid)]})

    def _compute_fulltext(self):
        """Used only to force fulltext into a function field."""
        return ''

    def _search_fulltext(self, operator, value):
        return ['|', '|',
                ('name', operator, value),
                ('description', operator, value),
                ('number', operator, value),
                ]

    @api.model
    def get_hierarchical_domain(self, parent_id):
        return [
            ('parent_id', '=', parent_id),
            ('type.has_children', '=', True),
            '|', '|',
            ('project_id.participant_ids', 'in', self.env.user.id),
            ('parent_id.participant_ids', 'in', self.env.user.id),
            ('participant_ids', 'in', self.env.user.id)
        ]

    @api.multi
    def action_hierarchy_dive(self):
        # #11382
        if not self.child_ids:
            return {}
        action = self.env.ref('anytracker.action_kanbans').read()[0]
        # context not correctly passed, forcing domain
        #action['context'] = dict(parent_id=self.id)
        action['domain'] = self.get_hierarchical_domain(self.id)
        return action

    @api.multi
    def action_hierarchy_up(self):
        # #11382
        action = self.env.ref('anytracker.action_kanbans').read()[0]
        if self.parent_id:
            # context not correctly passed, forcing domain
            # action['context'] = dict(parent_id=self.parent_id.parent_id)
            action['domain'] = self.get_hierarchical_domain(self.parent_id.parent_id.id)
        return action

    name = fields.Char(
        string='Title',
        track_visibility='onchange',
        required=True)
    number = fields.Integer(
        string='Number',
        track_visibility='onchange')
    type = fields.Many2one(
        'anytracker.ticket.type',
        string='Type',
        track_visibility='onchange',
        default=_default_type,
        required=True)
    permalink = fields.Char(
        compute=_get_permalink,
        track_visibility='onchange',
        string='Permalink', )
    description = fields.Text(
        string='Description')
    fulltext = fields.Text(
        compute='_compute_fulltext',
        search='_search_fulltext',
        store=False)
    create_date = fields.Datetime(
        string='Creation Time')
    write_date = fields.Datetime(
        string='Modification Time')
    subnode_ids = fields.One2many(
        'anytracker.ticket',
        readonly=True,
        string='Sub-nodes',
        compute=_subnode_ids)
    has_subnode = fields.Boolean(
        string='Has sub-nodes ?',
        compute=_has_subnode)
    shortened_description = fields.Text(
        string='Description',
        compute=_shortened_description)
    breadcrumb = fields.Char(
        search='_search_breadcrumb',
        string='Location',
        compute=_formatted_breadcrumb)
    relative_parent_breadcrumbs = fields.Char(
        string='Location',
        compute=_formatted_rparent_breadcrumb)
    # duration = fields.Selection(  # depreciated only used in history depreciated too
    #     [(0, '< half a day'),
    #      (None, 'Will be computed'),
    #      (1, 'Half a day')],
    #     default=0,
    #     string='duration')
    child_ids = fields.One2many(
        'anytracker.ticket',
        'parent_id',
        string='Sub-tickets',
        track_visibility='onchange')
    nb_children = fields.Integer(
        string='# of children',
        help='Number of children',
        compute=_nb_children)
    participant_ids = fields.Many2many(
        'res.users',
        'anytracker_ticket_assignment_rel',
        'ticket_id',
        'user_id',
        string='Participant')
    is_participant = fields.Boolean(
        'Is participant',
        compute=_is_participant)
    parent_id = fields.Many2one(
        'anytracker.ticket',
        string='Parent',
        default=_default_parent_id,
        ondelete='cascade')
    project_id = fields.Many2one(
        'anytracker.ticket',
        string='Project',
        ondelete='cascade',
        track_visibility='onchange',
        domain=[('parent_id', '=', False)],
        readonly=True)
    requester_id = fields.Many2one(
        'res.users',
        track_visibility='onchange',
        string='Requester')
    parent_left = fields.Integer(
        string='Parent Left',
        index=True)
    parent_right = fields.Integer(
        string='Parent Right',
        index=True)
    sequence = fields.Integer(
        string='sequence')
    active = fields.Boolean(
        'Active',
        default=True,
        help="Uncheck to make the project disappear, instead of deleting it")
    state = fields.Selection(
        [('running', 'Running'),
         ('trashed', 'Trashed')],
        string='State',
        default='running',
        required=True)
    icon = fields.Binary('anytracker.ticket.type', related='type.icon', )
    has_attachment = fields.Boolean(
        string='Has attachment ?',
        store=True,
        compute=_has_attachment)

    _sql_constraints = [
        ('number_uniq', 'unique(number)', 'Number must be unique!')]


class ResPartner(models.Model):
    """ Improve security
    """
    _inherit = 'res.partner'

    def _search_allowed_partners(self, operator, user_id):
        """ used in an ir_rule,
        so that customers only see users involved in their tickets.
        'involved' means that they are assigned the same tickets.
        (not sure about the relevancy of the "assignment" criterion)
        """
        cr = self.env.cr
        # list of partners corresponding to users
        # which are assigned to the same tickets than the provided user
        cr.execute(
            'SELECT distinct u.partner_id FROM res_users u, '
            'anytracker_ticket_assignment_rel m, '
            'anytracker_ticket_assignment_rel n '
            'WHERE m.user_id=%s AND u.id=n.user_id '
            'AND n.ticket_id=m.ticket_id;',
            (user_id,))
        return [('id', operator, tuple(a[0] for a in cr.fetchall()))]

    # gives the list of users authorized to access this partner
    anytracker_user_ids = fields.One2many(
        'res.users',
        'partner_id',
        compute=lambda *a, **kw: None,  # mandatory for search
        search='_search_allowed_partners',
        string='Users allowed to access this partner')


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        if values.get('model') == 'anytracker.ticket' and 'body' in values:
            values['body'] = add_permalinks(self.env.cr.dbname, values['body'])
        return super(MailMessage, self).create(values)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def __init_groups_for_customers(self, values):
        """if the 'customer' group is selected, we """
        group_customer = self.env.ref('anytracker.group_customer').id
        group_partner = self.env.ref('anytracker.group_partner').id
        group_portal = self.env.ref('base.group_portal').id
        sel_groups = [v for v in values.items()
                      if v[0].startswith('sel_groups_')]
        for group_id in (group_customer, group_partner):
            if any(['_' + str(group_id) in g[0]
                   and g[1] and group_id == g[1]
                   for g in sel_groups]):
                values = {k: v for k, v in values.items()
                          if not k.startswith('sel_groups_')
                          and not k.startswith('_in_group')}
                values['groups_id'] = [(6, 0, [group_id, group_portal])]
        return values

    @api.model
    def create(self, values):
        values2 = self.__init_groups_for_customers(values)
        res = super(ResUsers, self).create(values2)
        return res

    @api.multi
    def write(self, values):
        """ When setting an account as customer,
            unset all other groups except portal"""
        values2 = self.__init_groups_for_customers(values)
        res = super(ResUsers, self).write(values2)
        return res
