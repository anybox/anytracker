##############################################################################
#
#    anytracker module for OpenERP, Ticket module
#    Copyright (C) 2012-2013 Anybox (<https://anybox.fr>)
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
    'name': 'Anytracker',
    'version': '11.0.1.0.0',
    'author': 'Anybox',
    'website': 'https://anybox.fr',
    'category': 'Project Management',
    'sequence': 150,
    'depends': [
        'web',
        'web_widget_color',
        'base',
        # 'email_template',
        'analytic',
        # 'hr_timesheet_invoice',
    ],
    'images': [
        'images/anytracker.png',
        'images/ticket.png',
        'images/bouquet.png',
    ],
    'description': '''Project management application, which provides:

- Hierarchical ticket management
- Freemind import/export
- Email notification
- Hierarchical risk management
- Hierarchical progress management
- Complexity/evaluation management
- Impact/Importance management
- Priority management (timebox, deadline, milestone)
- Commenting through OpenChatter
- Assignment
- Kanban view at any level with breadcrumb
- Modifications history tracking
- Ticket invoicing through an analytic account

You can launch tests from a buildout with:

  $ ./bin/openerp_command run-tests -d dbname -m anytracker

Or, if you installed nose in your buildout

  $ ./bin/nosetests -d dbname -- addons-anytracker/anytracker/

Note: Anytracker includes some icons from the "fam fam fam silk" set,
provided under the terms of the Creative Commons Attribution 2.5 license at
http://www.famfamfam.com/lab/icons/silk/
''',
    'data': [
        # groups:
        'security/groups.xml',
        # data:
        'method/data.xml',
        'complexity/data.xml',
        'data.xml',
        'stage/data.xml',
        'importance/data.xml',
        'notify/data.xml',
        'priority/data.xml',
        'link/data.xml',
        # views
        'view.xml',
        'mindmap/wizard/import_mindmap.xml',
        'mindmap/wizard/export_mindmap.xml',
        'mindmap/wizard/serve_mindmap.xml',
        'method/view.xml',
        'stage/view.xml',
        'tagging/view.xml',
        'complexity/wizard/view.xml',
        'complexity/view.xml',
        'importance/view.xml',
        'assignment/view.xml',
        'notify/view.xml',
        'priority/view.xml',
        'bouquet/view.xml',
        'invoicing/view.xml',
        'link/view.xml',
        'report/ticket.xml',
        'report/bouquet.xml',
        # model access:
        'security/ir.model.access.csv',
        'method/ir.model.access.csv',
        'history/ir.model.access.csv',
        'stage/ir.model.access.csv',
        'tagging/ir.model.access.csv',
        'complexity/ir.model.access.csv',
        'importance/ir.model.access.csv',
        'assignment/ir.model.access.csv',
        'notify/ir.model.access.csv',
        'priority/ir.model.access.csv',
        'bouquet/ir.model.access.csv',
        'link/ir.model.access.csv',
        # security rules:
        'bouquet/ir_rule.xml',
        'security/ir_rule.xml',

    ],
    'test': [],
    'demo': [],
    "js": ["static/*/*.js", "static/*/js/*.js"],
    "css": ["static/*/css/*.css"],
    "qweb": [],
    'active': False,
    'installable': True,
    'application': True,
    'web_preload': True,

}
