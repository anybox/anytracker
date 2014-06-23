# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from xml import sax
from datetime import datetime
from cStringIO import StringIO
from base64 import b64decode
import time


class import_mindmap_wizard(osv.TransientModel):
    _name = 'import.mindmap.wizard'
    _description = 'Import mindmap .mm file into anytracker tree'
    _columns = {
        'ticket_id': fields.many2one(
            'anytracker.ticket', 'Ticket',
            help="Ticket that will be updated"),
        'import_method': fields.selection(
            [('update', 'Update the ticket tree'),
             ('insert', 'Insert under the ticket')],
            'Import method',
            required=True,
            help="You can either update a tree or insert the mindmap under an existing ticket"
        ),
        'mindmap_content': fields.binary(_('File'), required=True),
        'green_complexity': fields.many2one(
            'anytracker.complexity',
            'green complexity',
            required=True),
        'orange_complexity': fields.many2one(
            'anytracker.complexity',
            'orange complexity',
            required=True),
        'red_complexity': fields.many2one(
            'anytracker.complexity',
            'red complexity',
            required=True),
        'method_id': fields.many2one('anytracker.method', 'Project method', required=True),
    }
    _defaults = {
        'import_method': 'insert'
    }

    def execute_import(self, cr, uid, ids, context=None):
        '''Launch import of nn file from mindmap'''
        if isinstance(ids, (int, long)):
            ids = [ids]
        for wizard in self.browse(cr, uid, ids, context=context):
            complexity_dict = {'green_complexity_id': wizard.green_complexity.id or False,
                               'orange_complexity_id': wizard.orange_complexity.id or False,
                               'red_complexity_id': wizard.red_complexity.id or False,
                               }
            content_handler = FreemindContentHandler(cr, uid, self.pool, wizard, complexity_dict)
            error_handler = FreemindErrorHandler()
            sax.parse(StringIO(b64decode(wizard.mindmap_content)),
                      content_handler, error_handler)
        return {'type': 'ir.actions.act_window_close'}


class FreemindContentHandler(sax.ContentHandler):
    '''Handling event of sax xml parser'''

    rich_content_buffer = None

    def __init__(self, cr, uid, pool, wizard, complexity_dict):
        '''get element for access to openobject pool and db cursor'''
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.wizard = wizard
        self.import_method = wizard.import_method
        self.ticket_id = wizard.ticket_id.id if wizard.ticket_id else False
        self.parent_ids = []
        self.updated_ticket_ids = []
        self.complexity_dict = complexity_dict
        self.context = self.pool.get('res.users').context_get(cr, uid)
        self.context['import_mindmap'] = True
        stages = wizard.method_id.stage_ids
        self.initial_stage = sorted(stages,
                                    key=lambda x: x and x.sequence)[0].id if stages else False

    def startElement(self, name, attrs):
        names = attrs.getNames()
        ticket_pool = self.pool.get('anytracker.ticket')
        if name == 'node':
            text_name = ''
            if 'TEXT' in names:
                text_name = attrs.getValue("TEXT")
            else:
                text_name = ''
            if len(self.parent_ids) == 0:
                # first ticket
                if self.import_method == 'insert':
                    self.parent_id = self.ticket_id
                elif self.import_method == 'update':
                    if not self.ticket_id:
                        raise osv.except_osv(
                            _('Error'),
                            _("To be able to use update method, "
                              "you should set a parent ticket "
                              "on the export wizard"))
                    ticket = ticket_pool.browse(self.cr, self.uid, self.ticket_id, self.context)
                    self.parent_id = ticket.parent_id.id if ticket.parent_id else False
                else:
                    raise Exception('Bad import method')
            else:
                self.parent_id = self.parent_ids[-1:][0]['osv_id']

            modified_mindmap = datetime.fromtimestamp(int(attrs.getValue('MODIFIED'))/1000.0)
            modified_mindmap = datetime.strftime(modified_mindmap, '%Y-%m-%d %H:%M:%S')
            created_mindmap = datetime.fromtimestamp(int(attrs.getValue('CREATED'))/1000.0)
            created_mindmap = datetime.strftime(created_mindmap, '%Y-%m-%d %H:%M:%S')
            id_mindmap = attrs.getValue('ID')
            vals = {
                'name': text_name,
                'parent_id': self.parent_id,
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
            if self.parent_id:
                domain.append(('parent_id', '=', self.parent_id))
            elif self.ticket_id:
                domain.append(('id', '=', self.ticket_id))
            osv_id = ticket_pool.search(self.cr, self.uid, domain,
                                        context=self.context)
            if (not osv_id) or (not self.parent_id and not self.ticket_id):
                vals['method_id'] = self.wizard.method_id.id,
                osv_id = ticket_pool.create(self.cr, self.uid, vals, context=self.context)
            else:
                assert self.import_method == 'update', "Found existing ticket, but "
                "import method is not update"
                ticket_pool.write(self.cr, self.uid, osv_id, vals, context=self.context)
                osv_id = osv_id[0]
            self.parent_ids.append({'id': id_mindmap, 'osv_id': osv_id})
            self.updated_ticket_ids.append(osv_id)
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
                self.pool.get('anytracker.rating').create(
                    self.cr, self.uid,
                    {'ticket_id': self.parent_ids[-1:][0]['osv_id'],
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
        ticket_pool = self.pool.get('anytracker.ticket')
        if self.rich_content_buffer:
            self.rich_content_buffer[-1] = self.rich_content_buffer[-1].strip()
        if name == 'p':
            self.rich_content_buffer.append('\n')
        if name in ['node']:
            if len(self.parent_ids) != 0:
                self.parent_ids.pop()
        if name == 'richcontent':
            ticket_pool.write(
                self.cr, self.uid,
                self.parent_ids[-1:][0]['osv_id'],
                {'description': ''.join(self.rich_content_buffer)},
                context=self.context)
            self.rich_content_buffer = False
        if self.rich_content_buffer:
            self.rich_content_buffer.append('')

    def endDocument(self):
        ticket_obj = self.pool.get('anytracker.ticket')
        first_ticket_id = self.updated_ticket_ids[0]
        if self.ticket_id and self.ticket_id != first_ticket_id and self.import_method == 'update':
            raise osv.except_osv(_('Error'), _('You try to update the wrong main ticket'))
        domain = [
            ('id', 'child_of', first_ticket_id),  # children of main ticket
            ('id', 'not in', self.updated_ticket_ids),  # ticket not updated
        ]
        deleted_ticket_ids = ticket_obj.search(self.cr, self.uid, domain, context=self.context)
        ticket_obj.unlink(self.cr, self.uid, deleted_ticket_ids, context=self.context)


class FreemindErrorHandler(sax.ErrorHandler):
    '''Handling error event of sax xml parser'''

    def error(self, exception):
        "Handle a recoverable error."
        raise osv.except_osv(_('Error !'),
                             exception.args[0])

    def fatalError(self, exception):
        "Handle a non-recoverable error."
        raise osv.except_osv(_('Error !'),
                             exception.args[0])

    def warning(self, exception):
        "Handle a warning."
        raise osv.except_osv(_('Warning !'),
                             exception.args[0])
