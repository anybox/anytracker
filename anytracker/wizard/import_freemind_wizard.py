# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from xml.sax import ContentHandler, make_parser, ErrorHandler


class import_freemind_wizard(osv.osv_memory):
    _name = 'import.freemind.wizard'

    _description = 'Import freemind .mm file for generate anytracker tree'

    _columns = {
            'filename': fields.char(_('Filename'), size=128, required=True),
                }

    def execute_import(self, cr, uid, ids, context={}):
        '''Launch import of nn file from freemind'''
        for wiz_brw in self.browse(cr, uid, ids):
            path = wiz_brw.filename
            parser = make_parser()
            handler = freemind_content_handler(cr, uid, self.pool)
            handlerError = freemind_error_handler()
            parser.setContentHandler(handler)
            parser.setErrorHandler(handlerError)
            parser.parse(path)
        return {'type': 'ir.actions.act_window_close'}

import_freemind_wizard()


class freemind_content_handler(ContentHandler):
    '''Handling event of sax xml parser'''

    def __init__(self, cr, uid, pool):
        '''get element for access to openobject pool and db cursor'''
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.parent_ids = []
        self.project_root = True
        self.rich_content_buffer = False

    def startElement(self, name, attrs):
        names = attrs.getNames()
        any_tick_pool = self.pool.get('anytracker.ticket')
        any_complex_pool = self.pool.get('anytracker.ticket.complexity')
        if name in ['node']:
            text_name = ''
            if 'TEXT' in names:
                text_name = attrs.getValue("TEXT")
            else:
                text_name = ''
            if len(self.parent_ids) == 0:
                self.parent_id = False
            else:
                self.parent_id = self.parent_ids[-1:][0]['osv_id']
            osv_id = any_tick_pool.create(self.cr, self.uid, {
                                'name': text_name,
                                'infos': '',
                                'projectroot': self.project_root,
                                'workflow_id': 1,
                                'parent_id': self.parent_id
                                }
                                )
            if 'ID' in names:
                self.parent_ids.append({'id': attrs.getValue('ID'), 'osv_id': osv_id})
            else:
                self.parent_ids.append({'id': False, 'osv_id': osv_id})
            self.project_root = False
        # rich content
        if name in ['richcontent']:
            self.rich_content_buffer = ''
        if name in ['html','head', 'body', 'p']:
            self.rich_content_buffer += '<' + name + '>'
        # icon
        if name in ['icon']:
            icon = attrs.getValue('BUILTIN')
            if icon == 'flag-green':
                complexity_id = any_complex_pool.search(self.cr, self.uid,
                                                        [('rating', '=', 8)]
                                                        )[0]
            elif icon == 'flag-orange':
                complexity_id = any_complex_pool.search(self.cr, self.uid,
                                                        [('rating', '=', 34)]
                                                        )[0]
            elif icon == 'flag-red':
                complexity_id = any_complex_pool.search(self.cr, self.uid,
                                                        [('rating', '=', 89)]
                                                        )[0]
            else:
                complexity_id = False
            any_tick_pool.write(self.cr, self.uid, 
                        self.parent_ids[-1:][0]['osv_id'],
                            {'complexity_id' : complexity_id})

    def characters(self, content):
        content = content.strip()
        if content != '':
            if self.rich_content_buffer != False:
                self.rich_content_buffer += content


    def endElement(self, name):
        any_tick_pool = self.pool.get('anytracker.ticket')
        if name in ['node']:
            if len(self.parent_ids) == 0:
                self.project_root = True
            else:
                self.parent_ids.pop()
        # rich content
        if name in ['html','head', 'body', 'p']:
            self.rich_content_buffer += '</' + name + '>'
        if name in ['richcontent']:
            any_tick_pool.write(self.cr, self.uid, 
                            self.parent_ids[-1:][0]['osv_id'],
                                {
                                    'infos' : self.rich_content_buffer
                                }
                            )
            self.rich_content_buffer = False


class freemind_error_handler(ErrorHandler):
    '''Handling error event of sax xml parser'''

    def error(self, exception):
        "Handle a recoverable error."
        raise osv.except_osv(_('Error !'),
                        exception)

    def fatalError(self, exception):
        "Handle a non-recoverable error."
        raise osv.except_osv(_('Error !'),
                        exception)

    def warning(self, exception):
        "Handle a warning."
        raise osv.except_osv(_('Warning !'),
                        exception)

