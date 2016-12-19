# coding: utf-8
from openerp import models, fields


class Tag(models.Model):
    """Tags of a ticket.
    Used for analysis and expect to be used as transverse functional meanings
    """
    _name = 'anytracker.tag'

    name = fields.Char(
        'name',
        size=64,
        required=True,
        translate=True,
    )

    _sql_constraints = [
        ('tag_name_uniq', 'unique(name)', 'Tag name must be unique!'),
    ]


class Ticket(models.Model):
    """A ticket can be defined by multiple tags
    """

    _inherit = 'anytracker.ticket'

    tags = fields.Many2many(
        'anytracker.tag',
        string='Tags',
    )
