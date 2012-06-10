from osv import osv
from osv import fields

class method(osv.osv):
    """ Choice of project method
    such as GTD, anytracker, TMA, etc.
    """
    _name = "anytracker.method"
    _columns = {
        'code': fields.char('Name', size=32, help='Short name of the project management method'),
        'name': fields.char('Name', size=64, help='Name of the project management method'),
        }

class Ticket(osv.osv):
    """add method selection on tickets
    """
    _inherit = 'anytracker.ticket'

    _columns = {
        'method_id': fields.many2one('anytracker.method', 'Method', help='Project method'),
        'project_method_id': fields.related('project_id', 'method_id',
            readonly=True,
            type='many2one',
            relation='anytracker.method',
            string='Method of the project',
            help='Project method'),
        }
    
    def _get_default_method(self, cr, uid, context):
        code = context.get('method', 'gtd')
        method_ids = self.pool.get('anytracker.method').search(cr, uid, [('code','=',code)])
        if method_ids:
            return method_ids[0]
        return False

    _defaults = {
        'method_id': _get_default_method,
    }
