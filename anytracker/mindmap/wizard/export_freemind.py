from osv import osv, fields
import random
from tools.translate import _
from datetime import datetime

#TODO complexity icon, mindmapfile to binary?, richtext content generation
class export_freemind_wizard(osv.osv_memory):
    _name = 'export.freemind.wizard'
    _description = 'export freemind .mm file for generate by anytracker tree'
    _columns = {
        'ticket_id': fields.many2one('anytracker.ticket', 'Ticket', domain="[('parent_id', '=', False)]"),
        'mindmap_file': fields.char('Path of file to write', 256),
        'green_complexity': fields.many2one('anytracker.complexity', 'green complexity'),
        'orange_complexity': fields.many2one('anytracker.complexity', 'orange complexity'),
        'red_complexity': fields.many2one('anytracker.complexity', 'red complexity'),
    }

    def execute_export(self, cr, uid, ids, context=None):
        '''Launch export of nn file to freemind'''
        any_tick_complexity_pool = self.pool.get('anytracker.complexity')
        for wizard in self.browse(cr, uid, ids, context=context):
            complexity_dict = {'green_complexity_id': wizard.green_complexity.id or \
                                any_tick_complexity_pool.search(cr, uid, [('value', '=', 3)])[0],
                               'orange_complexity_id': wizard.orange_complexity.id or \
                                any_tick_complexity_pool.search(cr, uid, [('value', '=', 21   )])[0],
                               'red_complexity_id': wizard.red_complexity.id or \
                                any_tick_complexity_pool.search(cr, uid, [('value', '=', 3)])[0],
                               }
            ticket_id = wizard.ticket_id and wizard.ticket_id.id or False
            if not ticket_id:
                raise osv.except_osv('Error', 'Please select a ticket to export')
            fp = open(wizard.mindmap_file, 'wb')
            writer_handler = FreemindWriterHandler(cr, uid, self.pool, fp)
            writer_parser = FreemindParser(cr, uid, self.pool, writer_handler, ticket_id, complexity_dict)
            writer_parser.parse(cr, uid)
            fp.close()
        return {'type': 'ir.actions.act_window_close'}

export_freemind_wizard()

class FreemindParser():
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
            if ticket_write.has_key('child'):
                ticket_write.pop('child')
            self.handler.startElement('node', ticket_write)
            if ticket_d.has_key('child'):
                for ticket in ticket_d['child']:
                    recurs_ticket(ticket)
            self.handler.endElement('node')
        recurs_ticket(ticket_tree_ids[0])
        self.handler.endDocument()
        return True

def gMF(date):
    '''getMindmapDateFormat'''
    if not date:
        time = datetime.now()
    else:
        time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    mindmap_time = '1303' + str(time.toordinal()) + '000'
    return mindmap_time
    

from xml.sax.saxutils import XMLGenerator

class FreemindWriterHandler(XMLGenerator):
    '''For generate .mm file'''
    def __init__(self, cr, uid, pool, fp):
        self.pool = pool
        self.padding = 0
        XMLGenerator.__init__(self, fp, 'UTF-8')
        #super(FreemindWriterHandler, self).__init__(fp)

    def startDocument(self):
        startElement = '<' + 'map version="0.9.0"' + '>' + '\n\
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->\n' 
        self._out.write(startElement)
    
    def endDocument(self):
        stopElement = '</' + 'map' + '>' + '\n'
        self._out.write(stopElement)
    
    def startElement(self, tag, attrs={}):
        attrs_write = {'CREATED' :gMF(attrs['created_mindmap']),
                       'MODIFIED' : gMF(attrs['modified_mindmap']),
                       'ID' : attrs['id_mindmap'] or 'ID_' + str(random.randint(1, 10**10)),
                       'TEXT' : attrs['name'],
                       }
        try:
            XMLGenerator.startElement(self, tag, attrs_write)
        except:
            import pdb; pdb.set_trace()
        #super(FreemindWriterHandler, self).startElement(tag, attrs_write)

    def endElement(self, tag):
        XMLGenerator.endElement(self, tag)


