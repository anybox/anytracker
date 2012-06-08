# coding: utf-8
from osv import fields, osv
from tools.translate import _


class stage(osv.osv):

    _name = 'anytracker.stage'

    _columns = {
        'name': fields.char('name', size=64, required=True),
        'state': fields.char('state', size=64, required=True),
        'default': fields.boolean(_('Initial stage?')),
        'method_id': fields.many2one('anytracker.method', _('Project method')),
    }

    _defaults = {
         'default': lambda *a: False,
    }


class ticket(osv.osv):

    _inherit = 'anytracker.ticket'

    def _read_group_stage_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        """return stage names for the group_by_full directive
        """
        # XXX improve the filter to handle categories
        stage_osv = self.pool.get('anytracker.stage')
        stage_ids = stage_osv.search(cr, uid, [])
        stage_names = stage_osv.name_get(cr, access_rights_uid, stage_ids, context=context)
        return stage_names

    _columns = {
        'stage_id': fields.many2one('anytracker.stage', _('Stage')),
    }

    _group_by_full = {
        'stage_id': _read_group_stage_ids
    }

