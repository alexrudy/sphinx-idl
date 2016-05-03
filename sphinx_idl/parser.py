# -*- coding: utf-8 -*-
#
#  parser.py
#  sphinx-idl
#
#  Created by Alexander Rudy on 2014-11-13.
#  Copyright 2014 Alexander Rudy. All rights reserved.
#

import os.path
import re
import abc
import six
from docutils.parsers.rst import Directive, directives
from docutils import io, nodes, statemachine, utils

CompiledRE = type(re.compile(""))

@six.add_metaclass(abc.ABCMeta)
class IDLSourceLine(object):
    """A single line of IDL source"""
    def __init__(self, source):
        super(IDLSourceLine, self).__init__()
        self.parse(source)
    
    kind = None
    pattern = None
    
    @classmethod
    def match(cls, line):
        """docstring for match"""
        if cls.pattern is not None:
            return bool(cls.pattern.search(line))
        return True
    
    @abc.abstractmethod
    def parse(self, line):
        """Parse this line."""
        pass
        

class IDLComment(IDLSourceLine):
    """An IDL comment line."""
    
    kind = 'comment'
    
    pattern = re.compile(r"^\s*;[-+]?")
    
    def parse(self, line):
        """Parse line contents."""
        match = self.pattern.search(line)
        self.prefix = match.group(0)
        self.contents = line[len(match.group(0)):].strip("\r\n")
        
class IDLFunction(IDLSourceLine):
    """An IDL function definition"""
    
    kind = 'function'
    
    pattern = re.compile(r"^\s*function\s+(?P<name>[^\s,]+),\s?", re.IGNORECASE)
    
    def __repr__(self):
        if hasattr(self, 'name'):
            return "<{}: \"{}, {}\">".format(self.__class__.__name__, self.name, self.signature)
        return super(IDLFunction, self).__repr__()
        
    
    def parse(self, line):
        """Parse the function definition."""
        match = self.pattern.search(line)
        self.name = match.group(1)
        self.signature = line[len(match.group(0)):].strip("\r\n")

class IDLProgram(IDLSourceLine):
    """docstring for IDLProgram"""
    
    kind = 'pro'
    
    pattern = re.compile(r"^\s*pro\s+(?P<name>[^\s,]+),\s?", re.IGNORECASE)
    
    def __repr__(self):
        if hasattr(self, 'name'):
            return "<{}: \"{}, {}\">".format(self.__class__.__name__, self.name, self.signature)
        return super(IDLProgram, self).__repr__()
    
    def parse(self, line):
        """Parse the function definition."""
        match = self.pattern.search(line)
        self.name = match.group(1)
        self.signature = line[len(match.group(0)):].strip("\r\n")
        
class IDLSource(IDLSourceLine):
    
    kind = 'source'
    
    pattern = None
    
    def parse(self, line):
        """Parse source lines."""
        self.source = line
        

class IDLParser(object):
    """A **very simple** IDL source file parser."""
    
    line_patterns = [ IDLComment, IDLFunction, IDLProgram, IDLSource ]
    
    def __init__(self):
        super(IDLParser, self).__init__()
        
    def continue_lines(self, lines):
        """Handle source continuation."""
        continue_line = re.compile(r"\$[\n\r]*$")
        lineiter = iter(lines)
        for line in lineiter:
            while continue_line.search(line):
                line = line.rstrip("$\n\r") + lineiter.next()
            yield line
    
    def parse_single(self, line):
        """Parse a single source line."""
        for linecls in self.line_patterns:
            if linecls.match(line):
                return linecls(line)
    
    def parse(self, lines):
        """Parse many lines, emitting containers as we go."""
        comments = []
        for line in self.continue_lines(lines):
            obj = self.parse_single(line)
            
            if obj.kind == 'function' or obj.kind == 'pro':
                obj.docstring = "\n".join(comment.contents for comment in comments)
                yield obj
            
            if obj.kind == 'comment':
                comments.append(obj)
            else:
                comments = []
        
                