##############################################################################
#
#    anytracker module for OpenERP, Ticket module
#    Copyright (C) 2012-2013 Anybox (<http://www.anybox.fr>)
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
    'name': 'Anytracker Report',
    'version': '0.1',
    'author': 'Anybox',
    'website': 'http://anybox.fr',
    'category': 'Project Management',
    'sequence': 150,
    'depends': [
        'anytracker',
        'report_webkit',
    ],
    'images': [
    ],
    'description': '''Add reports to `Anytracker` a project management application
''',
    'data': [
        'webkit_report/header_footer.xml',
        'webkit_report.xml',
    ],
    'test': [],
    'demo': [],
    "js": [],
    "css": [],
    "qweb": [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
