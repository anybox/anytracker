# coding: utf-8
import re
import logging
from lxml import html
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from lxml import etree
from openerp import SUPERUSER_ID
from openerp.osv import orm

logger = logging.getLogger(__file__)

ticket_regex = re.compile('([Tt]icket ?#?)([\d]+)')


def add_permalinks(cr, string):
    # replace ticket numbers with permalinks
    if not string:
        return string
    return ticket_regex.subn(
        '<a href="/anytracker/%s/ticket/\\2">\\1\\2</a>' % cr.dbname,
        string)[0]


class Type(models.Model):
    """ Ticket type (project, ticket, deliverable, etc.)
    """
    _name = 'anytracker.ticket.type'

    name = fields.Char('Title', size=255, required=True)
    code = fields.Char('Code', size=255, required=True)
    description = fields.Text('Description')
    has_children = fields.Boolean('Can have children')
    default = fields.Boolean('Default for new tickets')
    icon = fields.Binary('Icon in the kanban')


class Ticket(models.Model):
    _name = 'anytracker.ticket'
    _description = "Anytracker tickets"
    _rec_name = 'breadcrumb'
    _order = 'priority ASC, importance DESC, sequence ASC, create_date DESC'  # more logical now
    _parent_store = True
    _inherit = ['mail.thread']

    def _ids_to_be_recalculated(self, cr, uid, ids, context=None):
        """ return list of id which will be recalculated """
        res = []
        for attachment in self.browse(cr, uid, ids):
            if attachment.res_model == 'anytracker.ticket':
                res.append(attachment.res_id)
        return res

    @api.one
    def _has_attachment(self, ):
        """ check if tickets have attachment(s) or not"""
        attach_model = self.env['ir.attachment']
        attachment_ids = attach_model.search([('res_id', '=', self.ids), ('res_model', '=', 'anytracker.ticket')])
        if not attachment_ids:
            self.has_attachment = False
        self.has_attachment = True

    @api.one
    def _shortened_description(self):
        """shortened description used in the list view and kanban view
        """
        limit = 150
        d = html.fromstring((self.description or '').strip() or '&nbsp;').text_content()
        self.shortened_description = d[:limit] + u'(…)' if len(d) > limit else d

    @api.one
    def get_breadcrumb(self):
        """ get all the parents up to the root ticket
        """
        # for ticket_id in [int(i) for i in ids]:
        self._cr.execute("WITH RECURSIVE parent(id, parent_id, name) as "
                   "(select 0, %s, text('') UNION SELECT t.id, t.parent_id, t.name "
                   " FROM parent p, anytracker_ticket t WHERE t.id=p.parent_id) "
                   "SELECT id, parent_id, name FROM parent WHERE id!=0", (self.id,))

        # The same using parent_store. Actually slower for our typical trees:
        # cr.execute("select b.id, b.parent_id, b.name "
        #           "from anytracker_ticket a join anytracker_ticket b "
        #           "on a.parent_left >= b.parent_left and a.parent_right<=b.parent_right "
        #           "and a.id=%s order by b.parent_left", (ticket_id,))
        res = [dict(zip(('id', 'parent_id', 'name'), line))
                          for line in reversed(self._cr.fetchall())]
        print(res)
        return res[0]

    @api.one
    def _formatted_breadcrumb(self):
        """ format the breadcrumb
        TODO : format in the view (in js)
        """
        res = {}
        breadcrumb = self.get_breadcrumb()
        self.breadcrumb = u' / '.join([b['name'] for b in breadcrumb])

    def _get_root(self, cr, uid, ticket_id, context=None):
        """Return the real root ticket (not the project_id of the ticket)
        """
        if not ticket_id:
            return False
        ticket = self.read(cr, uid, ticket_id, ['parent_id'], context,
                           load='_classic_write')
        parent_id = ticket.get('parent_id', False)
        if parent_id:
            breadcrumb = self.get_breadcrumb(cr, uid, [parent_id], context)[parent_id]
            if not breadcrumb:
                breadcrumb = [self.read(cr, uid, parent_id, ['name', 'parent_id'])]
            project_id = breadcrumb[0]['id']
        else:
            # if no parent, we are the project
            project_id = ticket_id
        return project_id

    def write(self, cr, uid, ids, values, context=None):
        """write the project_id when writing the parent.
        Also propagate the (in)active flag to the children
        """
        types = self.pool.get('anytracker.ticket.type')
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        children = None
        if 'parent_id' in values:
            root_id = self._get_root(cr, uid, values['parent_id'])
            values['project_id'] = root_id
            for ticket in self.browse(cr, uid, ids, context):
                if ticket.id == values['parent_id']:
                    raise except_orm(_('Error'),
                                     _(u"Think of yourself. Can you be your own parent?"))
                # if reparenting to False, propagate the current ticket as project for children
                project_id = root_id or ticket.id
                # set the project_id of me and all the children
                children = self.search(cr, uid, [('id', 'child_of', ticket.id)])
                super(Ticket, self).write(cr, uid, children, {'project_id': project_id})
                self.recompute_subtickets(cr, uid, values['parent_id'])
        if 'active' in values:
            for ticket_id in ids:
                children = self.search(cr, uid, [
                    ('id', 'child_of', ticket_id),
                    ('active', '=', not values['active'])])
                super(Ticket, self).write(cr, uid, children, {'active': values['active']})

        # replace ticket numbers with permalinks
        if 'description' in values:
            values['description'] = add_permalinks(cr, values['description'])

        # don't allow to set a node as ticket if it has children
        if values.get('type'):
            for ticket in self.browse(cr, uid, ids, context):
                if ticket.child_ids and not types.browse(cr, uid, values.get('type')).has_children:
                    del values['type']

        res = super(Ticket, self).write(cr, uid, ids, values, context=context)
        if 'parent_id' in values:
            for ticket in self.browse(cr, uid, ids, context):
                method_id = (ticket.parent_id.method_id.id
                             if values['parent_id'] is not False else ticket.method_id.id)
                super(Ticket, self).write(cr, uid, children, {'method_id': method_id})
        # correct the parent to be a node
        if 'parent_id' in values:
            type_ids = types.search(cr, uid, [('code', '=', 'node')])
            if type_ids:
                self.write(cr, uid, values['parent_id'], {'type': type_ids[0]})

        return res

    @api.one
    def _get_permalink(self):
        base_uri = '/anytracker/%s/ticket/' % self._cr.dbname
        self.permalink = base_uri + str(self.number)

    def create(self, cr, uid, values, context=None):
        """write the project_id when creating
        """
        types = self.pool.get('anytracker.ticket.type')
        type_ids = types.search(cr, uid, [('code', '=', 'node')])
        values.update({
            'number': self.pool.get('ir.sequence').next_by_code(cr, SUPERUSER_ID,
                                                                'anytracker.ticket'),
        })
        if 'parent_id' in values and values['parent_id']:
            project_id = self.read(cr, uid, values['parent_id'],
                                   ['project_id'], load='_classic_write')['project_id']
            values['project_id'] = project_id

        # project creation: auto-assign the 'node' type
        if not values.get('parent_id') and type_ids:
            values['type'] = type_ids[0]

        # replace ticket numbers with permalinks
        if 'description' in values:
            values['description'] = add_permalinks(cr, values['description'])

        ticket_id = super(Ticket, self).create(cr, uid, values, context=context)

        if not values.get('parent_id'):
            self.write(cr, uid, ticket_id, {'project_id': ticket_id})

        # turn the parent into a node
        if 'parent_id' in values and values['parent_id'] and type_ids:
            self.write(cr, uid, values['parent_id'], {'type': type_ids[0]})

        # subscribe project members
        participant_ids = self.browse(cr, uid, ticket_id).project_id.participant_ids
        if participant_ids:
            self.message_subscribe_users(cr, uid, [ticket_id], [p.id for p in participant_ids])

        return ticket_id

    def _default_parent_id(self, cr, uid, context=None):
        """When creating a ticket, return the current ticket as default parent
        or its parent if this is a leaf (to create a sibling)
        """
        active_id = context.get('active_id')
        if not active_id:
            return False
        ticket = self.browse(cr, uid, active_id)
        if not ticket.parent_id:
            return active_id
        elif not ticket.type.has_children:
            return ticket.parent_id.id
        else:
            return active_id

    def _default_type(self, cr, uid, context=None):
        types = self.pool.get('anytracker.ticket.type')
        type_ids = types.search(cr, uid, [('default', '=', True)])
        if not type_ids:
            return False
        return type_ids[0]

    @api.one
    def _subnode_ids(self):
        """Return the list of children that are themselves nodes."""
        self.subnode_ids = self.search([('parent_id', '=', self.ids), ('type.has_children', '=', True)])

    @api.one
    def _nb_children(self):
        nb_children = self.search([('id', 'child_of', self.ids)], count=True)
        self.nb_children = nb_children

    def _search_breadcrumb(self, operator, value):
        """Use the 'name' in the search function for the parent,
        instead of 'breadcrum' which is implicitly used because of the _rec_name
        """
        # assert (len(domain) == 1 and len(domain[0]) == 3)  # handle just this case
        # (f, o, v) = domain[0]
        return [('name', operator, value)]

    def onchange_parent(self, cr, uid, ids, parent_id, context=None):
        """ Fill the method when changing parent
        """
        context = context or {}
        if not parent_id:
            return {}
        method_id = self.read(cr, uid, parent_id, ['method_id'],
                              context, load='_classic_write')['method_id']
        return {'value': {'method_id': method_id}}

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """ Allow managers to set an empy parent_id (a project)
        """
        fvg = super(Ticket, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type,
            context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and fvg['type'] == 'form':
            access_obj = self.pool.get('ir.model.access')
            allow = (access_obj.check_groups(cr, uid, "anytracker.group_member")
                     or access_obj.check_groups(cr, uid, "anytracker.group_manager"))
            doc = etree.fromstring(fvg['arch'])
            try:
                node = doc.xpath("//field[@name='parent_id']")[0]
            except:
                logger.error("It seems you're using a broken version of OpenERP")
                return fvg
            orm.transfer_modifiers_to_node({'required': not allow}, node)
            fvg['arch'] = etree.tostring(doc)
        return fvg

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        """
            Overwrite the name_search function to search a ticket
            with their name or thier number
        """
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            ticket_ids = []
            if name.isdigit():
                number = int(name)
                ticket_ids = self.search(cr, uid, [('number', '=', number)] + args,
                                         limit=limit, context=context)
            else:
                ticket_ids = self.search(cr, uid, [('name', operator, name)] + args,
                                         limit=limit, context=context)
            if len(ticket_ids) > 0:
                return self.name_get(cr, uid, ticket_ids, context)
        return super(Ticket, self).name_search(cr, uid, name, args, operator=operator,
                                               context=context, limit=limit)

    def trash(self, cr, uid, ids, context=None):
        """ Trash the ticket
        set active = False, and move to the last stage
        """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        self.write(cr, uid, ids, {
            'active': False,
            'state': 'trashed',
            'progress': 100.0,
            'stage_id': False})
        self.recompute_parents(cr, uid, ids)

    def reactivate(self, cr, uid, ids, context=None):
        """ reactivate a trashed ticket
        """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        self.write(cr, uid, ids, {'active': True, 'state': 'running'})
        stages = self.pool.get('anytracker.stage')
        for ticket in self.browse(cr, uid, ids):
            start_ids = stages.search(cr, uid, [('method_id', '=', ticket.method_id.id),
                                                ('progress', '=', 0)])
            if len(start_ids) != 1:
                raise except_orm(_('Configuration error !'),
                                 _('One and only one stage should have a 0% progress'))
            # write stage in a separate line to let it recompute progress and risk
            ticket.write({'stage_id': start_ids[0]})
        self.recompute_parents(cr, uid, ids)

    def cron(self, cr, uid, context=None):
        """Anytracker CRON tasks
        To be overloaded by submodules
        """
        return

    name = fields.Char(string='Title',required=True)
    number = fields.Integer(string='Number')
    type = fields.Many2one(
        'anytracker.ticket.type',
        string='Type',
        required=True)
    permalink = fields.Char(compute='_get_permalink', string='Permalink', )
    description = fields.Text(string='Description', required=False)
    create_date = fields.Datetime(string='Creation Time')
    write_date = fields.Datetime(string='Modification Time')
    subnode_ids = fields.One2many('anytracker.ticket',
                                  readonly=True,
                                  string='Sub-nodes',
                                  compute='_subnode_ids')
    shortened_description = fields.Text(
        string='Description',
        compute='_shortened_description')
    breadcrumb = fields.Char(
        search='_search_breadcrumb',
        string='Location',
        compute='_formatted_breadcrumb')
    duration = fields.Selection(
        [(0, '< half a day'), (None, 'Will be computed'), (1, 'Half a day')],
        string='duration')
    child_ids = fields.One2many(
        'anytracker.ticket',
        'parent_id',
        string='Sub-tickets',
        required=False)
    nb_children = fields.Integer(
        string='# of children',
        help='Number of children',
        compute='_nb_children')
    participant_ids = fields.Many2many(
        'res.users',
        'anytracker_ticket_assignment_rel',
        'ticket_id',
        'user_id',
        string='Participant',
        required=False)
    parent_id = fields.Many2one(
        'anytracker.ticket',
        string='Parent',
        required=False,
        ondelete='cascade')
    project_id = fields.Many2one(
        'anytracker.ticket',
        string='Project',
        ondelete='cascade',
        domain=[('parent_id', '=', False)],
        readonly=True)
    requester_id = fields.Many2one(
        'res.users',
        string='Requester')
    parent_left = fields.Integer(string='Parent Left', )
    parent_right = fields.Integer(string='Parent Right', )
    sequence = fields.Integer(string='sequence')
    active = fields.Boolean('Active', help="Uncheck to make the project disappear, "
                                            "instead of deleting it")
    state = fields.Selection(
        [('running', 'Running'),
         ('trashed', 'Trashed')],
        string='State',
        required=True)
    icon = fields.Binary('anytracker.ticket.type',related='type.icon', )
    has_attachment = fields.Boolean(
        string='Has attachment ?',
        # store={'ir.attachment': (_ids_to_be_recalculated, ['res_id', 'res_model'], 10)},
        compute='_has_attachment')

    _defaults = {
        'type': _default_type,
        'duration': 0,
        'parent_id': _default_parent_id,
        'active': True,
        'state': 'running',
    }

    _sql_constraints = [('number_uniq', 'unique(number)', 'Number must be unique!')]


class ResPartner(models.Model):
    """ Improve security
    """
    _inherit = 'res.partner'

    def _anytracker_search_users(self, operator, value):
        # assert (len(domain) == 1 and domain[0][0] == 'anytracker_user_ids')
        # user_id = domain[0][2]
        # cr.execute('select distinct u.partner_id from res_users u, '
        #            'anytracker_ticket_assignment_rel m, anytracker_ticket_assignment_rel n '
        #            'where m.user_id=%s and u.id=n.user_id and n.ticket_id=m.ticket_id;',
        #            (user_id,))
        return [('name', operator, value)]

    anytracker_user_ids = fields.One2many('res.users',
                                          'user_id',
                                          search='_anytracker_search_users',
                                          string='Allowed users')


class MailMessage(models.Model):
    _inherit = 'mail.message'

    def create(self, cr, uid, values, context=None):
        if values.get('model') == 'anytracker.ticket' and 'body' in values:
            values['body'] = add_permalinks(cr, values['body'])
        return super(MailMessage, self).create(cr, uid, values, context)
