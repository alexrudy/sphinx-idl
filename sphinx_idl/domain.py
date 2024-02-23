# -*- coding: utf-8 -*-
# 
#  domain.py
#  sphinx-idl
#  
#  Created by Alexander Rudy on 2014-02-18.
#  Copyright 2014 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import re
import itertools
# from docutils import nodes
from docutils.parsers.rst import directives, Directive
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.domains import Domain, ObjType
from sphinx.domains.python import _pseudo_parse_arglist
from sphinx.locale import _
from sphinx.util.docfields import GroupedField, TypedField, Field
from sphinx.util.nodes import make_refnode

__all__ = ['setup', 'IDLDomain', 'IDLFunction', 'IDLProgram']

idl_sig_re = re.compile(
    r'''^ (?:(pro|function)\s)?     # pro/function specifier
          ([\w_]*)           # pro/function name
          (?:,?\s*(.*)            # optional: arguments
          )? $                          # and nothing more
          ''', re.VERBOSE | re.IGNORECASE)

idl_struct_re = re.compile(
  r'''^(?:([\w_]*)\s*=)?   # structure variable identifier
      \s*{\s*              # structure opens
      (?:([\w_]*)\s*)?     # structure name (optional)
      (?:,\s*([\w_]*:.+))* # Variables in the structure
      \s*}\s*$             # structure closes (variables described below)
  '''
, re.VERBOSE)

idl_member_re = re.compile(
    r'''
    ([\w_]*\.)?
    ([\w_]*)
    '''
, re.VERBOSE)

class IDLObjectBase(ObjectDescription):
    """Base class for any IDL object."""
    
    display_prefix = None
    parentname_set = False
    
    def add_target_and_index(self, names, sig, signode):
        name, parent = names
        fullname = name
        if fullname not in self.state.document.ids:
            if fullname not in signode.get('names',[]):
                signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            inv = self.env.domaindata['idl']['objects']
            if fullname in inv:
                self.state_machine.reporter.warning(
                    'duplicate idl description of %s, ' % name +
                    'other instance in ' + self.env.doc2path(inv[fullname][0]),
                    line=self.lineno)
            inv[fullname] = (self.env.docname, self.objtype)
        
        indextext = "{1} ({0})".format(self.objtype, fullname)
        self.indexnode['entries'].append(('single', indextext, fullname, '', None))
        
    def after_content(self):
        if self.parentname_set:
            self.env.temp_data['idl:parent'] = None
    
class IDLStruct(IDLObjectBase):
    """Describes an IDL structure"""
    
    display_prefix = None
    
    doc_field_types = [
        TypedField('parameter', label=_('Parameters'),
                   names=('param', 'parameter',),
                   typerolename='obj', typenames=('paramtype', 'type'),),
    ]
    
    def handle_signature(self, sig, signode):
        """Handle IDL signature lines"""
        m = idl_struct_re.match(sig)
        if not m:
            self.env.app.warn("Signature did not match for {}".format(sig))
            raise ValueError("Signature did not match!")
        variable, name, contents = m.groups()
        
        if not (variable or name):
            raise ValueError("Structure must have a variable name, or a name.")
        
        # Add a prefix for function/program
        if self.display_prefix:
            signode += addnodes.desc_annotation(self.display_prefix,
                                                self.display_prefix)
        
        signode += addnodes.desc_annotation(self.objtype, self.objtype)
        signode['names'] = []
        
        if variable:
            signode += addnodes.desc_name(variable, variable)
            signode += addnodes.desc_addname(" = "," = ")
            signode['names'] += [variable]
            
        
        signode += addnodes.desc_addname("{", "{")
        if name:
            signode += addnodes.desc_name(name, name)
            # Register the full name of the program
            signode['names'] += [name]
        signode += addnodes.desc_addname("}", "}")
        
        fullname = signode['names'][0]
        signode['fullname'] = fullname
        
        return fullname, ''
    
    def before_content(self):
        IDLObjectBase.before_content(self)
        if self.names:
            self.env.temp_data['idl:parent'] = self.names[0][0]
            self.parentname_set = True

class IDLMember(IDLObjectBase):
    """A member of an IDL structure."""
    
    def handle_signature(self, sig, signode):
        """Handle member signature."""
        
        m = idl_member_re.match(sig)
        if not m:
            self.env.app.warn("Signature did not match for {}".format(sig))
            raise ValueError("Signature did not match!")
        struct, name = m.groups()
        
        structname = self.env.temp_data.get('idl:parent')
        if structname:
            if struct and struct.startswith(structname):
                fullname = struct + name
                # class name is given again in the signature
                struct = struct[len(structname):].lstrip('.')
            elif struct:
                # class name is given in the signature, but different
                # (shouldn't happen)
                fullname = structname + '.' + struct + name
            else:
                # class name is not given in the signature
                fullname = structname + '.' + name
        else:
            if struct:
                structname = struct.rstrip('.')
                fullname = struct + name
            else:
                structname = ''
                fullname = name

        signode['struct'] = structname
        signode['fullname'] = fullname
        
        if struct:
            signode += addnodes.desc_addname(struct, struct)
        
        signode += addnodes.desc_name(name, name)
        
        return (fullname, structname)

class IDLObject(IDLObjectBase):
    """An IDL program or function. """
    
    display_prefix = None
    
    doc_field_types = [
        TypedField('parameter', label=_('Parameters'),
                   names=('param', 'parameter', 'arg', 'argument',),
                   typerolename='obj', typenames=('paramtype', 'type'),),
        TypedField('keyword', label=_('Keywords'),
                   names=('keyword', 'kwarg', 'kwparam'),
                   typerolename='obj', typenames=('paramtype', 'type'),),
       GroupedField('flag', label=_('Flags'),
                  names=('flag', 'switch'),),
    ]
    
    def handle_signature(self, sig, signode):
        """Handle IDL signature lines"""
        m = idl_sig_re.match(sig)
        if not m:
            self.env.app.warn("Signature did not match for {}".format(sig))
            raise ValueError("Signature did not match!")
        pro_or_function, name, arglist = m.groups()
        
        # Add a prefix for function/program
        if self.display_prefix:
            signode += addnodes.desc_annotation(self.display_prefix,
                                                self.display_prefix)
        
        signode += addnodes.desc_annotation(self.objtype, self.objtype)
        
        # Register the full name of the program
        signode['fullname'] = name
        signode += addnodes.desc_name(name, name)
        
        # Parse the argument list from the signature
        if not arglist and self.objtype == 'function':
            signode += addnodes.desc_parameterlist()
        elif arglist:
            _pseudo_parse_arglist(signode, arglist)
        return (name, '')
        

class IDLProgram(IDLObject):
    """An IDL Program"""
    
    doc_field_types = IDLObject.doc_field_types + [
        TypedField('returnvariable', label=_('Return Variables'), rolename='obj',
               names=('var', 'ivar', 'cvar'),
               typerolename='obj', typenames=('vartype',),
               can_collapse=True),
    ]


class IDLFunction(IDLObject):
    
    doc_field_types = IDLObject.doc_field_types + [
        Field('returnvalue', label=_('Returns'), has_arg=False,
              names=('returns', 'return')),
        Field('returntype', label=_('Return type'), has_arg=False,
              names=('rtype',)),
    ]
    
    

class IDLXRefRole(XRefRole):
    
    def process_link(self, env, refnode, has_explicit_title, title, target):
        refnode['idl:parent'] = env.temp_data.get('idl:parent')
        if not has_explicit_title:
            title = title.lstrip('.')   # only has a meaning for the target
            target = target.lstrip('~') # only has a meaning for the title
            # if the first character is a tilde, don't display the module/class
            # parts of the contents
            if title[0:1] == '~':
                title = title[1:]
                dot = title.rfind('.')
                if dot != -1:
                    title = title[dot+1:]
        return title, target

class IDLDomain(Domain):
    """IDL language domain."""
    name = 'idl'
    label = 'IDL'
    
    object_types = {
        'function': ObjType(_('function'), 'func'),
        'pro':   ObjType(_('pro'),'pro'),
        'structure': ObjType(_('structure'), 'struct'),
        'member': ObjType(_('member'), 'member')
    }

    directives = {
        'function': IDLFunction,
        'pro':  IDLProgram,
        'structure' : IDLStruct,
        'member': IDLMember,
    }
    roles = {
        'func' :  IDLXRefRole(),
        'pro': IDLXRefRole(fix_parens=False),
        'struct': IDLXRefRole(fix_parens=False),
        'member': IDLXRefRole(fix_parens=False)
    }
    
    initial_data = {
        'objects': {},  # fullname -> docname, objtype
    }

    def clear_doc(self, docname):
        for fullname, (fn, _) in self.data['objects'].items():
            if fn == docname:
                del self.data['objects'][fullname]


    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        
        parent = node.get('idl:parent')
        if parent:
            ptarget = parent + '.' + target
        if parent and (ptarget in self.data['objects']):
            obj = self.data['objects'][ptarget]
            return make_refnode(builder, fromdocname, obj[0], ptarget,
                                contnode, ptarget)
        elif target in self.data['objects']:
            obj = self.data['objects'][target]
            return make_refnode(builder, fromdocname, obj[0], target,
                                contnode, target)
        return None
    
    def get_objects(self):
        for refname, (docname, type) in self.data['objects'].items():
            yield (refname, refname, type, docname, refname, 1)

def setup(app):
    app.add_domain(IDLDomain)