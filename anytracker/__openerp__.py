##############################################################################
#
#    anytracker module for OpenERP, Ticket module
#    Copyright (C) 2012 Anybox (<http://www.anybox.fr>)
#                Colin GOUTTE <cgoute@anybox.fr>
#                Christophe COMBELLES <ccomb@anybox.fr>
#                Simon ANDRE <sandre@anybox.fr>
#                Jean Sebastien SUZANNE <jssuzanne@anybox.fr>
#
#    This file is a part of anytracker
#
#    anytracker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    anytracker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
        'name' : 'anytracker',
        'version' : '0.1',
        'author' : 'Anybox',
        'website' : 'http://anybox.fr',
        'category' : 'Generic Modules/Others',
        'depends' : [
            'base',
        ],
        'description' : 'Hierarchical task manager',
        'init_xml' : [],
        'demo_xml' : [],
        'update_xml' : [
            'security/ir.model.access.csv',
            'anytracker_view.xml',
            'wizard/import_freemind_wizard.xml',
            'wizard/export_freemind_wizard.xml',
            #data
            'data/complexity.xml',
            'data/workflow1.xml',
        ],
        'active': False,
        'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
