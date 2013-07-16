#!/usr/bin/env python

from .parser import parse_snippet
from . import types

def collect(nodes, placeholders, mirrors):
    for node in nodes:
        if isinstance(node, types.PlaceholderType):
            if node.index not in placeholders:
                placeholders[node.index] = node
            mirrors.setdefault(node.index, []).append(node)
            collect(node.content, placeholders, mirrors)
        elif isinstance(node, types.PlaceholderChoiceType):
            placeholders[node.index] = node
            mirrors.setdefault(node.index, []).append(node)
        elif isinstance(node, types.PlaceholderTransformType):
            mirrors.setdefault(node.index, []).append(node)

class Snippet(object):
    def __init__(self, source):
        self.nodes = parse_snippet(source)
        self.placeholders = {}
        self.mirrors = {}
        collect(self.nodes, self.placeholders, self.mirrors)
        
    def __str__(self):
        return "".join([str(node) for node in self.nodes])
    
    def replace(self, processor, memo):
        return "".join([node.replace(processor, self.placeholders, None, memo) for node in self.nodes])

    __unicode__ = __str__
        