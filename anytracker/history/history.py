# coding: utf-8
from openerp import models, fields, _
from openerp.exceptions import except_orm
import time


class History(models.Model):
    _name = 'anytracker.history'
    _description = 'History of ticket'

    create_uid = fields.Many2one(
        'res.users',
        'User',
        readonly=True)
    create_date = fields.Datetime(
        'Create Date',
        readonly=True)
    modification = fields.Text(
        'Modification',
        readonly=True)


class Ticket(models.Model):
    _inherit = 'anytracker.ticket'

    history_ids = fields.Many2many(
        'anytracker.history',
        'anytracker_ticket_history_rel',
        'ticket_id',
        'history_id',
        'History')

    def _add_history(self, values):
        vals = ""
        if self.env.context.get('import_mindmap', False):
            vals += _("Update from Import MindMap\n")

        def _all2many(name, model, val):
            if not val:
                return ""
            vals = _('Modify field %s\n') % name
            OBJ = self.env[model]
            for v in val:
                vals += " => "
                if v[0] == 0:
                    vals += _('Create new value %s') % v[2].get('name')
                elif v[0] == 1:
                    iname = v[2].get('name')
                    if not iname:
                        iname = OBJ.browse(v[1]).name_get()
                    vals += _('Modify value %s') % iname
                elif v[0] == 2:
                    iname = OBJ.browse(v[1]).name_get()
                    vals += _('Remove value %s') % iname
                elif v[0] == 3:
                    iname = OBJ.browse(v[1]).name_get()
                    vals += _('Unlink value %s') % iname
                elif v[0] == 4:
                    iname = OBJ.browse(v[1]).name_get()
                    vals += _('Link value %s') % iname
                elif v[0] == 5:
                    iname = OBJ.browse(v[1]).name_get()
                    vals += _('Unlink all value %s') % iname
                elif v[0] == 6:
                    iname = OBJ.browse(v[1]).name_get()
                    vals += _('Unlink all value  and add:') % iname
                    for y, z in iname:
                        vals += '\n   * ' + z

                vals += '\n'

            return vals

        def _many2one(fieldname, model, val):
            if not val:
                return ""
            OBJ = self.env[model]
            nameget = OBJ.browse(val).name_get()
            return _('Modify field %s with new valeur %s\n'
                     ) % (fieldname, nameget)

        for k, v in values.items():
            if k == 'stage_id':
                vals += _many2one(k, 'anytracker.stage', v)
            elif k == 'history_ids':
                continue
            elif k == 'parent_id':
                vals += _many2one(k, 'anytracker.ticket', v)
            elif k == 'requester_id':
                vals += _many2one(k, 'res.users', v)
            elif k == 'child_ids':
                vals += _all2many(k, 'anytracker.ticket', v)
            # elif k == 'duration':
            #    col = dict(self._columns[k].selection)
            #    vals += _('Modify field %s with new valeur %s\n'
            #              ) % (k, col.get(v))
            else:
                vals += _('Modify field %s with new valeur %s\n') % (k, v)

        values['history_ids'] = [(0, 0, {'modification': vals})]
        return values

    def create(self, values):
        if values.get('id_mindmap'):
            # Created by import
            values['modified_openerp'] = values.get('modified_mindmap')
        else:
            # TODO generate id_mindmap
            # TODO generate time
            pass
        values = self._add_history(values)
        return super(Ticket, self).create(values)

    def write(self, values):

        WATCH = ('name', 'description', 'rating_ids', 'stage_id', 'parent_id')

        if values.get('modified_mindmap'):
            for item in self.read(['name', 'modified_openerp']):
                if values['modified_mindmap'] < item['modified_openerp']:
                    raise except_orm(_('Error'),
                                     _('You can t update the ticket %s'
                                       ) % item['name'])
        elif self.env.context.get('import_mindmap', False):
            # description and complexity
            pass  # TODO
        elif any(values.get(f) for f in WATCH):
            values['modified_openerp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        values = self._add_history(values)
        return super(Ticket, self).write(values)
