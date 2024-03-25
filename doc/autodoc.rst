Automatically documenting IDL
=============================

Automatically documenting IDL can be done by placing specially formatted comments in your IDL source files, and then asking sphinx to automatically read those comments from source.

Source documentation format
---------------------------

.. highlight:: idl

There is a very simple IDL source documentation parser implemented in parser.py, which will scan your IDL source files and extract docstrings by looking for comments which immediately preceede a function or procedure definition. It will use these comments as the restructured-text formatted documentation for that function or procedure. For example, an IDL file ``bench_view.pro`` containing this will produce automatic documentation for a procedure named ``bench_view``::

    ;+
    ; Display diagnostic windows which show the current state of the test bench.
    ;
    ; Views:
    ;
    ; - :pro:`bench_wfs_view`
    ; - :pro:`bench_dms_view`
    ; - :pro:`psf_view`
    ;
    ; :keyword NOPSF: Prevent taking a PSF image.
    ; :keyword TB: The test bench state structure. (see :func:`get_test_bench`)
    ;-
    pro bench_view, NOWFS=NOWFS, NOPSF=NOPSF, TB=TB
      compile_opt idl2
      TB = get_test_bench(TB=TB)
      if ~keyword_set(NOWFS) then r=bench_phase(TB=TB)
      bench_wfs_view, TB=TB
      bench_dms_view, TB=TB
      if ~keyword_set(NOPSF) then psf_view, TB=TB
    end


.. note:: Any comment which directly precedes the procedure or function definition will be used. The IDL continuous comment style (``;+`` and ``;-``) is not required for the parser to recognize it as a docstring. Note that the docstrings are formatted in restructured text, and not the IDLDOC format.

Source inclusion directives
---------------------------

To generate documentation from your IDL soruce file, add one of the following directives to your restructured text documentation. Both directives accept a path relative to the documentation root folder.

.. rst:directive:: .. idl:autofile:: path/to/idl/file.pro

    Include automatically generated documentation from an IDL file at ``path/to/idl/file.pro``.

    The option ``:summary:`` includes a table summary of all functions in a file at the beginning.

    The option ``:absolute:`` can be used to require an absolute file path.

.. rst:directive:: .. idl:autopath:: path/to/directory/of/idl/files/

    Include automatically generated documentation for every IDL file (``*.pro``) in the given path.

    The option ``:summary:`` includes a table summary of all functions in the files at the beginning of the documentation.

    The option ``:absolute:`` can be used to require an absolute file path.
