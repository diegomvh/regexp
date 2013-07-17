#!/usr/bin/env python

from .parser import parse_format_string
from . import types

class FormatString(object):
    def __init__(self, source):
        self.nodes = parse_format_string(source)
        
    def __str__(self):
        return "".join([str(node) for node in self.nodes])

    __unicode__ = __str__
        
    def replace(self, memodict):
        return "".join([node.replace(memodict) for node in self.nodes])
    
    def render(self, visitor, memodict):
        visitor.insertText(self.replace(memodict))
        