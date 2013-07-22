#!/usr/bin/env python

from .parser import parse_format_string
from . import types
from .base import compileRegexp

class FormatString(object):
    def __init__(self, source):
        self.nodes = parse_format_string(source)
        
    def __str__(self):
        return "".join([unicode(node) for node in self.nodes])

    __unicode__ = __str__
        
    def replace(self, sourceString, pattern, repeat = False, variables = None):
        text = ""
        memodict = {}
        pattern = compileRegexp(pattern)
        match = pattern.search(sourceString)
        while match:
            text += "".join([node.replace(memodict, match = match, variables = variables) for node in self.nodes])
            if not repeat:
                break
            match = pattern.search(sourceString, match.end())
        return text
    
    def render(self, visitor, memodict):
        visitor.insertText(self.replace(memodict))
        