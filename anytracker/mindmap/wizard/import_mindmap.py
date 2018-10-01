# -*- coding: utf-8 -*-
import time
from base64 import b64decode
from datetime import datetime
from io import BytesIO
from xml import sax

from odoo import api, fields, models,  _
from odoo.exceptions import UserError, ValidationError


class ImportMindmapWizard(models.TransientModel):
    _name = 'import.mindmap.wizard'
    _description = 'Import mindmap .mm file into anytracker tree'

    ticket_id = fields.Many2one(
        'anytracker.ticket', 'Ticket',
        help="Ticket that will be updated")
    import_method = fields.Selection(
        [('update', 'Update the ticket tree'),
         ('insert', 'Insert under the ticket')],
        'Import method',
        required=True,
        default='insert',
        help=_("You can either update a tree or insert "
               "the mindmap under an existing ticket"))
    mindmap_content = fields.Binary(
        _('File'),
        required=True)
    green_complexity = fields.Many2one(
        'anytracker.complexity',
        'green complexity',
        required=True)
    orange_complexity = fields.Many2one(
        'anytracker.complexity',
        'orange complexity',
        required=True)
    red_complexity = fields.Many2one(
        'anytracker.complexity',
        'red complexity',
        required=True)
    method_id = fields.Many2one(
        'anytracker.method',
        'Project method',
        required=True)

    # @api.multi
    # def execute_import(self, vals):
    #    '''Launch import of nn file from mindmap'''
    #    for wizard in vals:
    #        handler = FreemindContentHandler(wizard)
    #        error_handler = FreemindErrorHandler()
    #        sax.parse(BytesIO(b64decode(wizard.mindmap_content)),
    #                  handler, error_handler)
    #    return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create(self, vals):
        """override save/create function"""
        imported_mm = super(ImportMindmapWizard, self).create(vals)
        for wizard in imported_mm:
            handler = FreemindContentHandler(wizard)
            error_handler = FreemindErrorHandler()
            sax.parse(BytesIO(b64decode(wizard.mindmap_content)),
                      handler, error_handler)
        return imported_mm
        #return {'type': 'ir.actions.act_window_close'}


class FreemindContentHandler(sax.ContentHandler):
    '''Handling event of sax xml parser'''

    rich_content_buffer = None

    def __init__(self, wizard):
        self.wiz = wizard
        self.TICKET = self.wiz.env['anytracker.ticket']
        self.TICKET = self.TICKET.with_context({'import_mindmap': True})
        self.ticket = self.wiz.ticket_id
        self.parent_ids = []
        self.updated_ticket_ids = []
        self.complexity_dict = {
            'green_complexity_id': wizard.green_complexity.id or False,
            'orange_complexity_id': wizard.orange_complexity.id or False,
            'red_complexity_id': wizard.red_complexity.id or False}
        self.initial_stage = sorted(
            wizard.method_id.stage_ids,
            key=lambda x: x and x.sequence
            )[0].id if wizard.method_id.stage_ids else False

    def startElement(self, name, attrs):
        """TOO COMPLEX (cyclomatic 18) !!!
        """
        names = attrs.getNames()
        if name == 'node':
            text_name = ''
            if 'TEXT' in names:
                text_name = attrs.getValue("TEXT")
            else:
                text_name = ''
            if len(self.parent_ids) == 0:
                # first ticket
                if self.wiz.import_method == 'insert':
                    self.parent = self.ticket
                elif self.wiz.import_method == 'update':
                    if not self.ticket:
                        raise UserError(
                            _("To be able to use update method, "
                              "you should set a parent ticket "
                              "on the export wizard"))
                    self.parent = self.ticket.parent_id
                else:
                    raise Exception('Bad import method')
            else:
                self.parent = self.TICKET.browse(
                    self.parent_ids[-1:][0]['orm_id'])

            modified_mindmap = datetime.fromtimestamp(
                int(attrs.getValue('MODIFIED')) / 1000.0)
            modified_mindmap = datetime.strftime(
                modified_mindmap, '%Y-%m-%d %H:%M:%S')
            created_mindmap = datetime.fromtimestamp(
                int(attrs.getValue('CREATED')) / 1000.0)
            created_mindmap = datetime.strftime(
                created_mindmap, '%Y-%m-%d %H:%M:%S')
            id_mindmap = attrs.getValue('ID')
            vals = {
                'name': text_name,
                'parent_id': self.parent.id,
                'id_mindmap': id_mindmap,
                'modified_mindmap': modified_mindmap,
                'created_mindmap': created_mindmap,
                'modified_openerp': modified_mindmap,
                'stage_id': self.initial_stage,
            }
            # construct the domain to search the ticket
            # and update it or create a new one
            domain = [
                ('id_mindmap', '=', id_mindmap),
                ('created_mindmap', '=', created_mindmap),
            ]
            if self.parent:
                domain.append(('parent_id', '=', self.parent.id))
            elif self.ticket:
                domain.append(('id', '=', self.ticket.id))
            orm_id = self.TICKET.search(domain)
            if (not orm_id) or (not self.parent and not self.ticket):
                vals['method_id'] = self.wiz.method_id.id,
                orm_id = self.TICKET.create(vals).id
            else:
                assert self.wiz.import_method == 'update', "Found ticket, but "
                "import method is not update"
                self.TICKET.browse(orm_id).write(vals)
                orm_id = orm_id[0]
            self.parent_ids.append({'id': id_mindmap, 'orm_id': orm_id})
            self.updated_ticket_ids.append(orm_id)
        # rich content
        if name == 'richcontent':
            self.rich_content_buffer = ['']
        if name == 'br':
            self.rich_content_buffer[-1] += '\n'
        # icon
        if name == 'icon':
            icon = attrs.getValue('BUILTIN')
            if icon == 'flag-green':
                complexity_id = self.complexity_dict['green_complexity_id']
            elif icon == 'flag-orange':
                complexity_id = self.complexity_dict['orange_complexity_id']
            elif icon == 'flag-red':
                complexity_id = self.complexity_dict['red_complexity_id']
            else:
                complexity_id = False
            if complexity_id:
                self.wiz.env['anytracker.rating'].create(
                    self.cr, self.uid,
                    {'ticket_id': self.parent_ids[-1:][0]['orm_id'],
                     'complexity_id': complexity_id,
                     'user_id': self.uid,
                     'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                     },
                    context=self.context)
        if self.rich_content_buffer:
            self.rich_content_buffer[-1] = self.rich_content_buffer[-1].strip()
            self.rich_content_buffer.append('')

    def characters(self, content):
        if self.rich_content_buffer and content.strip != '':
            self.rich_content_buffer[-1] += content.replace('\n', ' ')

    def endElement(self, name):
        if self.rich_content_buffer:
            self.rich_content_buffer[-1] = self.rich_content_buffer[-1].strip()
        if name == 'p':
            self.rich_content_buffer.append('\n')
        if name in ['node']:
            if len(self.parent_ids) != 0:
                self.parent_ids.pop()
        if name == 'richcontent':
            self.TICKET.browse(self.parent_ids[-1:][0]['orm_id']).write(
                {'description': ''.join(self.rich_content_buffer)})
            self.rich_content_buffer = False
        if self.rich_content_buffer:
            self.rich_content_buffer.append('')

    def endDocument(self):
        first_ticket_id = self.updated_ticket_ids[0]
        if (self.ticket
                and self.ticket.id != first_ticket_id
                and self.wiz.import_method == 'update'):
            raise UserError(
                _('You try to update the wrong main ticket'))
        domain = [
            ('id', 'child_of', first_ticket_id),  # children of main ticket
            ('id', 'not in', self.updated_ticket_ids),  # ticket not updated
        ]
        deleted_ticket_ids = self.TICKET.search(domain)
        self.TICKET.browse(deleted_ticket_ids).unlink()


class FreemindErrorHandler(sax.ErrorHandler):
    '''Handling error event of sax xml parser'''

    def error(self, exception):
        "Handle a recoverable error."
        raise ValidationError(exception.args[0])

    def fatalError(self, exception):
        "Handle a non-recoverable error."
        raise ValidationError(exception.args[0])

    def warning(self, exception):
        "Handle a warning."
        raise ValidationError(exception.args[0])
