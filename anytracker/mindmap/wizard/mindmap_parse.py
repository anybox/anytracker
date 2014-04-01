# -*- coding: utf-8 -*-
from xml.sax.saxutils import XMLGenerator
import random
import time


class FreemindParser(object):
    '''Parse openerp project'''
    def __init__(self, cr, uid, pool, handler, ticket_id, complexity_dict):
        self.handler = handler
        self.pool = pool
        self.ticket_id = ticket_id
        self.complexity_dict = complexity_dict

    def parse(self, cr, uid):
        ticket_osv = self.pool.get('anytracker.ticket')
        self.handler.startDocument()
        ticket_tree_ids = ticket_osv.makeTreeData(cr, uid, [self.ticket_id])

        def recurs_ticket(ticket_d):
            ticket_write = ticket_d.copy()
            if 'child' in ticket_write:
                ticket_write.pop('child')
            self.handler.startElement('node', ticket_write)
            if 'child' in ticket_d:
                for ticket in ticket_d['child']:
                    recurs_ticket(ticket)
            self.handler.endElement('node')
        recurs_ticket(ticket_tree_ids[0])
        self.handler.endDocument()
        return True


def gMF(date):
    '''getMindmapDateFormat

    input: OpenERP string date/time format
    output: str of decimal representation of Epoch-based timestamp milliseconds, rounded.
    '''
    timestamp = time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S')) if date else time.time()
    return '%d' % (timestamp * 1000)


class FreemindWriterHandler(XMLGenerator):
    '''For generate .mm file'''
    def __init__(self, cr, uid, pool, fp):
        self.pool = pool
        self.padding = 0
        XMLGenerator.__init__(self, fp, 'UTF-8')

    def startDocument(self):
        startElement = '''<map version="0.9.0">
<!-- To view this file, download FreeMind from http://freemind.sourceforge.net -->
'''
        self._write(startElement.decode())

    def endDocument(self):
        stopElement = '</' + 'map' + '>' + '\n'
        self._write(stopElement.decode())

    def startElement(self, tag, attrs={}):
        attrs_write = {'CREATED': gMF(attrs['created_mindmap']),
                       'MODIFIED': gMF(max(attrs['modified_mindmap'],
                                           attrs['modified_openerp'])),
                       'ID': attrs['id_mindmap'] or 'ID_' + str(random.randint(1, 10**10)),
                       'TEXT': attrs['name'],
                       }
        XMLGenerator.startElement(self, tag, attrs_write)

    def endElement(self, tag):
        XMLGenerator.endElement(self, tag)
