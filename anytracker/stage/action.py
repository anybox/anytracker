from osv import fields, osv


class ActionStage(osv.Model):

    mapping = {'rating_ok': 'move_to_validate',
               'rating_ko': 'move_to_rating'}

    _name = 'anytracker.stage.action'
    _columns = {'name': fields.char('Name', required=True),
                'stage_ids': fields.many2many('anytracker.stage',
                                              id1='stage_id',
                                              id2='stage_action_id',
                                              string='Binded stages'),
                'button_label': fields.char('Label of the button', required=True),
                'function': fields.char('Name of the function to call', required=True)}
