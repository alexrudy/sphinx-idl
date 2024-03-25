Installing ``sphinx-idl``
=========================

To install sphinx-idl, get the package from source, then use the standard python ``setup.py`` file::

    $ python setup.py install


This will place ``sphinx-idl`` in the correct place on your python path.

Using ``sphinx-idl``
====================

Sphinx-IDL provides 2 sphinx extsions, ``sphinx_idl.domain``, which provides an IDL restructured text domain, and ``sphinx_idl.auto`` which automatically extracts documentation from IDL files. ``sphinx_idl.auto`` reqiures ``sphinx_idl.domain`` to run properly.

To use these extensions, add them to the list of extensions in your ``conf.py`` file::

    extensions = ['sphinx_idl.domain', 'sphinx_idl.auto']
