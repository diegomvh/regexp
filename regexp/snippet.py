#!/usr/bin/env python

from .parser import parse_snippet

class Snippet(object):
    def __init__(self, source):
        self.nodes = parse_snippet(source)
        
    def __str__(self):
        return "".join([str(node) for node in self.nodes])
    
    __unicode__ = __str__
        