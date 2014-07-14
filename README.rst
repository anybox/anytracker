Anytracker
==========

Anytracker is an open-source agile/lean project management tool available as an
Odoo module, developped and used by `Anybox <http://anybox.fr>`_.

It provides:

- Hierarchical ticket management
- Kanban view at any level with breadcrumb
- Customer access with clean project separation
- Freemind import/export
- Email notifications
- Hierarchical risk management
- Hierarchical progress management
- Complexity/evaluation management
- Importance management (impact or value)
- Priority management (timebox, deadline, milestone)
- Commenting through OpenChatter
- Assignment
- Modifications history tracking
- Ticket invoicing through an analytic account

About the design
================

Hierarchy of tickets
~~~~~~~~~~~~~~~~~~~~

The initial design decision of Anytracker was to use a hierarchical
representation of tickets, with a uniform model: a project is a ticket and each
ticket can have subtickets. It allows to split a big project into subprojects,
features, subfeatures, tickets, and split again a ticket when it is considered
too big.

The kanban view can display only tickets at a specific level in the hierarchy,
to focus on a specific sub-node of the project.

Separate submodules
~~~~~~~~~~~~~~~~~~~
Different features are split into submodules, using inheritance as if they were
real separate modules. It allows to more easily test and modify the different
features independently.

Few dependencies
~~~~~~~~~~~~~~~~

This tools has been kept separate and independant as most as possible from
standard Odoo modules. It allowed us to evolve from OpenERP 6.0 to latest
versions without too much work and easy migration path. Dependency on a few
standard Odoo modules has only been introduced recently for invoicing features.


Tests
=====

You can run the tests from a buildout with:

  $ ./bin/openerp_command run-tests -d dbname -m anytracker

Or, if you installed nose in your buildout

  $ ./bin/nosetests -d dbname -- addons-anytracker/anytracker/

Credits, contributing
=====================

Contributors:

- Christophe Combelles
- Florent Jouatte
- Georges Racinet
- Jean-Sébastien Suzanne
- Simon André
- Colin Goutte
- Clovis Nzouendjou Nana
- Pierre Verkest

Other contributions (with tests) are welcome from anyone through Bitbucket pull requests.

Anytracker includes some icons from the "fam fam fam silk" set,
provided under the terms of the Creative Commons Attribution 2.5 license at
http://www.famfamfam.com/lab/icons/silk/

