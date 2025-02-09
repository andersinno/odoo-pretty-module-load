Pretty Module Loading - Odoo Addon
==================================

Implement a pretty progress bar during Odoo module loading from the
terminal.  Provides much cleaner output when doing Odoo module
maintenance operations from the terminal.


Installation
------------

You may install this package with Pip::

    pip install odoo-pretty-module-load


Usage
-----

Call the ``pretty_module_load`` subcommand instead of the regular
``odoo -i modules`` or ``odoo -u modules``.

For example::

    odoo pretty_module_load -i my_module,another_module

Note: ``--stop-after-init`` is not needed, since it's added by default.

There is also subcommands ``module-install`` and ``module-update`` which
can be used to install or update modules.  They accept the module names
as arguments and don't need commas between module names.

Additionally alias subcommands ``i`` and ``u`` are provided to save some
typing::

    odoo u all
    odoo i module1 module2

The ``module-update`` and its alias ``u`` allow updating only the
changed modules.  That is also the default mode if no module names are
given.  This makes the common operation of updating all of the changed
modules very simple by just typing::

    odoo u

This detecting and updating of only changed modules relies on
`click-odoo-contrib`_ addon, which then needs to be installed.

.. _click-odoo-contrib: https://github.com/acsone/click-odoo-contrib


Verbosity
---------

The ``-v`` flag can be used to set the verbosity level.  To make the
command even more verbose ``-vv``, ``-vvv``  / ``-v1``, ``-v2``, ... can
be used. Using ``-v0`` suppresses all progress prints so that only
warnings and errors are shown.

Example::

    odoo u all -v


Environment Variables
---------------------

``PML_FORCE_ASCII``
  Use ASCII output if set to ``1`` or ``true``
