#
#  autoidl.py
#  sphinx-idl
#
#  Created by Alexander Rudy on 2014-11-13.
#  Copyright 2014 Alexander Rudy. All rights reserved.
#

import os.path
import glob
from docutils.parsers.rst import Directive, directives
from docutils import io, nodes, utils
from docutils.statemachine import ViewList
from docutils.utils.error_reporting import SafeString, ErrorString
from sphinx import addnodes
from sphinx.ext.autosummary import autosummary_table

from .parser import IDLParser

__all__ = ["setup", "IDLAutoFile", "IDLAutoPath"]


class IDLAutoBase(Directive):
    """A base class for IDLAuto tools"""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {"encoding": directives.encoding, "absolute": directives.flag, "summary": directives.flag}

    def read(self, path):
        """Read the file."""
        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning('"%s" directive disabled.' % self.name)

        path = directives.path(path)
        if False:
            source = self.state_machine.input_lines.source(self.lineno - self.state_machine.input_offset - 1)
            source_dir = os.path.dirname(os.path.abspath(source))
            path = os.path.normpath(os.path.join(source_dir, path))
        path = utils.relative_path(None, path)
        path = nodes.reprunicode(path)
        encoding = self.options.get("encoding", self.state.document.settings.input_encoding)
        e_handler = self.state.document.settings.input_encoding_error_handler
        try:
            self.state.document.settings.record_dependencies.add(path)
            include_file = io.FileInput(source_path=path, encoding=encoding, error_handler=e_handler)
        except UnicodeEncodeError:
            raise self.severe(
                'Problems with "%s" directive path:\n'
                'Cannot encode input file path "%s" '
                "(wrong locale?)." % (self.name, SafeString(path))
            )
        except OSError as error:
            raise self.severe(f'Problems with "{self.name}" directive path:\n{ErrorString(error)}.')
        return include_file

    def get_row(self, *column_texts):
        """Get the nodes for an individual table row."""
        row = nodes.row("")
        for text in column_texts:
            node = nodes.paragraph("")
            vl = ViewList()
            vl.append(text, "<autosummary>")
            self.state.nested_parse(vl, 0, node)
            try:
                if isinstance(node[0], nodes.paragraph):
                    node = node[0]
            except IndexError:
                pass
            row.append(nodes.entry("", node))
        return row

    def get_table(self):
        """docstring for get_table"""
        table_spec = addnodes.tabular_col_spec()
        table_spec["spec"] = "ll"

        table = autosummary_table("")
        real_table = nodes.table("", classes=["longtable"])
        table.append(real_table)
        group = nodes.tgroup("", cols=2)
        real_table.append(group)
        group.append(nodes.colspec("", colwidth=10))
        group.append(nodes.colspec("", colwidth=90))
        body = nodes.tbody("")
        group.append(body)
        return table_spec, table, body

    def handle_idl_object_table(self, obj):
        """docstring for handle_idl_object_table"""
        if obj.kind == "pro":
            signature_line = f":idl:pro:`{obj.name}`"
        elif obj.kind == "function":
            signature_line = f":idl:func:`{obj.name}`"
        try:
            summary_line = obj.docstring.strip().splitlines()[0]
        except IndexError:
            summary_line = " "
        return signature_line, summary_line

    def handle_idl_object(self, obj):
        """docstring for handle_idl_object"""
        tab_width = self.state.document.settings.tab_width
        if obj.kind == "pro":
            directive_line = f".. idl:pro:: pro {obj.name}, {obj.signature}"
        elif obj.kind == "function":
            directive_line = f".. idl:function:: function {obj.name}, {obj.signature}"
        content_lines = [" "] + obj.docstring.splitlines()
        content_lines = [(" " * tab_width) + line for line in content_lines]
        return [directive_line] + content_lines

    def get_idl_objects(self, include_file):
        """docstring for get_idl_objects"""
        parser = IDLParser()
        return parser.parse(include_file.readlines())


class IDLAutoFile(IDLAutoBase):
    """Automatically handle IDL files which contain functions or programs."""

    def get_lines(self, include_file):
        """Get lines for insertion"""
        newlines = []
        for obj in self.get_idl_objects(include_file):
            newlines += self.handle_idl_object(obj)
        return newlines

    def run(self):
        """Run this directive, loading the source etc."""
        include_file = self.read(self.arguments[0])
        newlines = []
        nodes = []
        if "summary" in self.options:
            table_spec, table, body = self.get_table()
            nodes += [table_spec, table]
        for obj in self.get_idl_objects(include_file):
            newlines += self.handle_idl_object(obj)
            if "summary" in self.options:
                body.append(self.get_row(*self.handle_idl_object_table(obj)))
        self.state_machine.insert_input(newlines, include_file.source_path)
        return nodes


class IDLAutoPath(IDLAutoBase):
    """Walk a directory path, and find things that match a given extension, then document them!"""

    option_spec = {
        "encoding": directives.encoding,
        "absolute": directives.flag,
        "glob": directives.unchanged,
        "summary": directives.flag,
    }

    def get_path(self):
        """docstring for get_path"""
        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning('"%s" directive disabled.' % self.name)
        source = self.state_machine.input_lines.source(self.lineno - self.state_machine.input_offset - 1)
        source_dir = os.path.dirname(os.path.abspath(source))
        path = directives.path(self.arguments[0])
        if not self.options.get("absolute", True):
            path = os.path.normpath(os.path.join(source_dir, path))
        path = utils.relative_path(None, path)
        path = nodes.reprunicode(path)
        globpath = self.options.get("glob", "*.pro")
        return os.path.join(path, globpath)

    def run(self):
        """Walk a directory and find many files!"""
        path = self.get_path()
        nodes = []
        body = None
        if "summary" in self.options:
            table_spec, table, body = self.get_table()
            nodes += [table_spec, table]
            self.options.pop("summary")
            for file in glob.glob(path):
                include_file = self.read(file)
                for obj in self.get_idl_objects(include_file):
                    body.append(self.get_row(*self.handle_idl_object_table(obj)))
        for file in reversed(glob.glob(path)):
            autofile = IDLAutoFile(
                self.name,
                [file],  # arguments
                self.options,
                [],  # content
                self.lineno,
                self.content_offset,
                self.block_text,
                self.state,
                self.state_machine,
            )
            nodes += autofile.run()
        return nodes


def setup(app):
    """Patch in this directive to the domain."""
    app.add_directive_to_domain("idl", "autofile", IDLAutoFile)
    app.add_directive_to_domain("idl", "autopath", IDLAutoPath)
