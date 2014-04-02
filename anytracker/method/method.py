from openerp.osv import osv
from openerp.osv import fields


class Method(osv.Model):
    """ Choice of project method
    such as GTD, anytracker, TMA, etc.
    """
    _name = "anytracker.method"
    _columns = {
        'code': fields.char('Name', size=32, help='Short name of the project management method'),
        'name': fields.char('Name', size=64, help='Name of the project management method'),
        'description': fields.text('Description', help='Description of the method'),
        'stage_ids': fields.one2many('anytracker.stage', 'method_id', 'Available stages'),
    }


class Ticket(osv.Model):
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
            raise osv.except_osv('Error', 'You must choose the method of the project')
        return super(Ticket, self).create(cr, uid, data, context)

    def write(self, cr, uid, ids, data, context=None):
        """Forbid to change the method (unexpected results)
        """
        if 'method_id' in data:
            raise osv.except_osv('Error', 'You cannot change the method of a project')
        return super(Ticket, self).write(cr, uid, ids, data, context)

    _columns = {
        'method_id': fields.many2one('anytracker.method', 'Method', help='Project method',
                                     ondelete="restrict"),
        'project_method_id': fields.related(
            'project_id', 'method_id', readonly=True, type='many2one',
            relation='anytracker.method',
            string='Method of the project', help='Project method'),
    }
