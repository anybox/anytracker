##############################################################################
#
#    anytracker module for OpenERP, Ticket module
#    Copyright (C) 2012 Anibox (<http://www.anybox.fr>)
#                Colin GOUTTE <cgoute@anybox.fr>
#                Christophe COMBELLES <ccomb@anybox.fr>
#                Simon ANDRE <sandre@anybox.fr>
#                Jean Sebastien SUZANNE <jssuzanne@anybox.fr>
#
#    This file is a part of anytracker
#
#    anytracker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    anytracker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _


class complexity(osv.osv):
    _name = 'anytracker.ticket.complexity'
    _columns = {
        'name': fields.char('Name', size=3, required=True),
        'rating': fields.float('Rating of time taking'),
        }

complexity()


class workflow1(osv.osv):
    _name = 'anytracker.ticket.workflow1'

    _columns = {
        'name': fields.char('name', size=64, required=True),
        'state': fields.char('state', size=64, required=True)
    }

workflow1()


class ticket_history(osv.osv):
    _name = 'ticket.history'
    _description = 'History of ticket'

    _columns = {
        'create_uid': fields.many2one('res.users', 'User', readonly=True),
        'create_date': fields.datetime('Create Date', readonly=True),
        'modification': fields.text('Modification', readonly=True),
    }


class ticket(osv.osv):
    _name = 'anytracker.ticket'
    _description = "Tickets for project management"

    def siblings(self, cr, uid, ids, field_name, args, context=None):
        # res = self.parent.chidlen.pop(self)
        #for nodes in si c'est le parent on prend les fils
        # on renvoit la liste des fils sans l'appelant
        #retourner un dict
        res = {}
        tickets = self.browse(cr, uid, ids, context)
        for t in tickets:
            res[t.id] = False
            if t.parent_id.id != False:
                res[t.id] = t.parent_id.id
                bros = [b.id for b in t.parent_id.child_ids]
                bros.remove(t.id)
                res[t.id] = bros
        return res

    _columns = {
        'name': fields.char('task name', 255, required=True),
        'infos': fields.text('task description', required=False),
        'state': fields.char('state', 30, required=False),
        'siblings': fields.function(siblings, type='many2many', obj='anytracker.ticket', string='Siblings', method=True),
        'projectroot': fields.boolean('is the root node', required=False),
        'duration': fields.selection([(0, '< half a day'), (None, 'Will be computed'), (1, 'Half a day')], 'duration'),
        'child_ids': fields.one2many('anytracker.ticket', 'parent_id', 'children', required=False),
        'assignedto_ids': fields.many2many('res.users', 'ticket_assignement_rel', 'ticket_id', 'user_id', required=False),
        'parent_id': fields.many2one('anytracker.ticket', 'parent', required=False),
        'requester_id': fields.many2one('res.users', 'Requester'),
        'complexity_id': fields.many2one('anytracker.ticket.complexity', 'complexity'),
        'workflow_id': fields.many2one('anytracker.ticket.workflow1', 'kanban_status', required=True),
        'history_ids': fields.many2many('ticket.history', 'ticket_ticket_history_rel', 'ticket_id', 'history_id', 'History'),
    }
    #complexity should be a many2many table, so a as to make is possibilble for various users (assignees) to rate different tickets.
    _defaults = {
        'state': 'Analyse',
        'duration': 0,
        }

    def _autoroot(self, cr, uid, ids, context=None):
        """
        eases the process of checking constraints so as to guess the only possible root when applies
        """
        orphans = self._orphans(cr, uid, ids, context=context)
        roots = self._roots(cr, uid, ids, context=context)
        if len(oprhans) == 1:
            if not roots:
                orphans[0].set_root()
                return True
        else:
            return False

    def _check_roots_orphans(self, cr, uid, ids, context=None):
        roots = self._roots(cr, uid, ids, context)
        orphans = self._orphans(cr, uid, ids, context)
        if len(roots) == 1 and len(orphans) == 1:
            if roots[0].id == orphans[0].id:
                return True
        return False

    def _easy_check(self, cr, uid, context=None):
        return self._check_root_orphans(cr, uid, context=None
           ) or self._autoroot(cr, uid, context=None)

    def link_to_parent(self, cr, uid, **kw):
        pass

    def link_to_child(self, cr, uid, **kw):
        pass

    def split(self, cr, uid, **kw):
        pass

    def _roots(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        result = []
        for node in nodes:
            if node.projectroot:
                result.append(node)
        return result

    def _orphans(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        orphans = []
        for node in nodes:
            if not node.parents:
                orphans.append(node)
        return orphans

    def _set_root(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'root': True}, context=context)

    def _check_roots(self, cr, uid, ids, context=None):
        roots = _roots(self, cd, uid, ids, context=context)
        if len(roots) == 1:
            return True
        else:
            return False

        #'duration': fields.selection([(0, '< half a day'), (None, 'Will be computed'), (1, 'Half a day')], 'duration'),
    def _add_history(self, cr, uid, values, context=None):
        vals = ""
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
            elif k == 'complexity_id':
                vals += _many2one(k, 'anytracker.ticket.complexity', v)
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

    def create(self, cr, uid, values, context=None):
        values = self._add_history(cr, uid, values, context=context)
        return super(ticket, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        values = self._add_history(cr, uid, values, context=context)
        return super(ticket, self).write(cr, uid, ids, values, context=context)

#=========================================================================
#Devrait renvoyer Bool,roots afin de de pas appeler deux fois _roots
#une fois pour la verif et une fois pour savoir quels sont les noeuds
#en cause
#========================================================================

ticket()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
