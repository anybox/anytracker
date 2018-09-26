# -*- coding: utf-8 -*-
from xml.sax.saxutils import XMLGenerator
from random import randint
import time


class FreemindParser(object):
    '''Parse openerp project'''
    def __init__(self, handler, wizard):
        self.wiz = wizard
        self.handler = handler
        self.complexity_dict = self.wiz.complexity_dict  # TODO unused?

    def parse(self):
        self.handler.startDocument()
        ticket_tree_ids = self.wiz.ticket_id.makeTreeData()

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
    output: str of decimal repr of Epoch-based timestamp milliseconds, rounded.
    '''
    timestamp = time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S')
                            ) if date else time.time()
    return '%d' % (timestamp * 1000)


class FreemindWriterHandler(XMLGenerator):
    '''For generate .mm file'''
    def __init__(self, fp):
        self.padding = 0
        XMLGenerator.__init__(self, fp, 'UTF-8')

    def startDocument(self):
        startElement = '''<map version="0.9.0">
<!-- To view this file, download FreeMind from http://freemind.sourceforge.net -->
'''
        self._write(startElement)

    def endDocument(self):
        stopElement = '</' + 'map' + '>' + '\n'
        self._write(stopElement)

    def startElement(self, tag, attrs={}):
        attrs_write = {
            'CREATED': gMF(attrs['created_mindmap']),
            'MODIFIED': gMF(max(attrs['modified_mindmap'],
                                attrs['modified_openerp'])),
            'ID': attrs['id_mindmap'] or 'ID_' + str(randint(1, 10**10)),
            'TEXT': attrs['name']}
        XMLGenerator.startElement(self, tag, attrs_write)

    def endElement(self, tag):
        XMLGenerator.endElement(self, tag)
