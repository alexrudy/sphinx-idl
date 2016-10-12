.. highlight:: rst

Directive Referenece
====================

The IDL Sphinx extension as several directives to describe the IDL language, and several directives for automatically generating documentaiton from IDL source files.

Language Directives
-------------------

.. rst:directive:: .. idl:pro:: name, argument, keyword=keyword

    Describes an IDL procedure `name` with a signature requiring arguments `argument` and keyword arguments `keyword`.

    This directive accepts `informational field lists`_ like the python directive :rst:dir:`py:function`.

    To use this directive in an RST document, use something like::

        .. idl:pro:: make_grids, g, n, center=center

            Make an `n` by `n` grid. If `center`, grid center is at 0,0

            :param g: The output variable for the grid.
            :param n: The size of the grid.
            :keyword center: Whether to center the keyword.

.. rst:directive:: .. idl:function:: name(argument, keyword=keyword)

    Describes an IDL function `name` with a signature requiring arguments `argument` and keyword arguments `keyword`.

    This directive accepts `informational field lists`_ like the python directive :rst:dir:`py:function`.

    To use this directive in an RST document, use something like::

        .. idl:function:: recenter(image, x, y)

            Recenter an image so that pixel `x`,`y` is at the center.

            :param image: A 2-D image array.
            :param x: The x position to center.
            :param y: The x position to center.
            :returns: A new image, centered on x, y.


.. rst:role:: idl:func

    Cross reference a function

.. rst:role:: idl:pro

    Cross reference a procedure.

.. _informational field lists: http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists
