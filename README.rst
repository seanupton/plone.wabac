==============================================================================
plone.wabac
==============================================================================

plone.wabac ("way-back") is a transitional package providing an add-on
for a new kind of "undo" in Plone.  It provides a means of logging
deletion metadata and restoring items that have been deleted to a previous
known state, using a ZODB history, but not ZODB's native undo feature,
which has known complications in complex real world scenarios.

It is the hope of this add-on's author that such functionality can be
proposed for implementation in a future Plone release (PLIP), and
enhanced with additional community contribution.

plone.wabac relies on zc.beforestorage and has the ability to undo to any
checkpoint in your (kept) pack history.

Features
--------

- Keeps a log of deletion metadata.  This metadata can be pruned by user
  action to remove items earlier than your pack history.  However, such
  history of deletion may be enumerated beyond capacity to restore, if
  useful as an audit trail.

- Can restore content and minimal path dependencies from previous snapshots
  of your system state (transactions).

- Is able to restore both deleted and modified content.

- Allows a user with the "Site Administrator" role to restore one or more
  deleted and/or modified items to previous state, easily with selection.

- Application-level restoration does not require or utilize ZODB
  transactional undo; rather, restoration uses standard content APIs,
  but makes efforts to preserve original unique identifiers of restored
  objects.

Documentation
-------------

This product is an early proof of concept, and documentation will be
forthcoming, in part based on presentation of this functionality at the
2016 Plone Digital Experience Conference.


Installation
------------

Install plone.wabac by adding it to your buildout::

    [buildout]
    ...
    eggs =
        plone.wabac


and then running ``bin/buildout``

After installation in your buildout, use the add-ons control panel to enable 
this add-on for your site.

Contribute
----------

- Issue Tracker: https://github.com/plone/plone.wabac/issues
- Source Code: https://github.com/plone/plone.wabac
- Documentation: TBD


Support
-------

For now, email project maintainer(s): sdupton@gmail.com


License
-------

Copyright 2016, Plone Foundation.  The project is licensed under the GPLv2.
