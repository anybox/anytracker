from osv import fields, osv
from tools.translate import _

class Stage(osv.osv):
    """Add progress value to the stage
    """
    _inherit = 'anytracker.stage'
    _columns = {
        'progress': fields.float('Progress', help='Progress value of the ticket reaching this stage'),
    }

class Ticket(osv.osv):
    """Add progress functionnality to tickets
    Progress is based on stages. Each stage has a progress,
    and the progress is copied on the ticket
    """
    _inherit = 'anytracker.ticket'

    def write(self, cr, uid, ids, values, context=None):
        """Climb the tree from the ticket to the root
        and recompute the progress of parents
        """
        if 'stage_id' in values:
            old_progress = dict([(t.id, t.stage_id.progress) for t in self.browse(cr, uid, ids, context)])

        res = super(Ticket, self).write(cr, uid, ids, values, context)

        if 'stage_id' not in values:
            return res
        for ticket in self.browse(cr, uid, ids, context):
            ticket.write({'progress': ticket.stage_id.progress})
            parent = ticket.parent_id
            #loop up to the root
            while parent:
                child_ids = self.search(cr, uid, [('id', 'child_of', parent.id),
                                                  ('child_ids', '=', False),
                                                  ('id', '!=', parent.id)])
                progression = (ticket.stage_id.progress - old_progress[ticket.id])/len(child_ids)
                new_progress = parent.progress + progression
                new_progress = 100.0 if new_progress > 100.0 else new_progress
                new_progress = 0.0 if new_progress < 0.0 else new_progress
                parent.write({'progress': new_progress})
                parent = parent.parent_id
        return res

    _columns = { 
        'progress': fields.float('Progress'),
     }
