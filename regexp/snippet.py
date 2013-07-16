#!/usr/bin/env python

from .parser import parse_snippet
from . import types

def collect(nodes, placeholders):
    for node in nodes:
        if isinstance(node, (types.PlaceholderType, types.PlaceholderChoiceType)):
            if node.index not in placeholders:
                placeholders[node.index] = node
            if isinstance(node, types.PlaceholderType):
                collect(node.content, placeholders)

class Snippet(object):
    def __init__(self, source):
        self.nodes = parse_snippet(source)
        self.placeholders = {}
        collect(self.nodes, self.placeholders)
        if '0' not in self.placeholders:
            self.placeholders['0'] = types.PlaceholderType("0")
            self.nodes.append(self.placeholders['0'])

    def __str__(self):
        return "".join([str(node) for node in self.nodes])

    def replace(self, processor, memo):
        return "".join([node.replace(processor, self.placeholders, None, memo) for node in self.nodes])

    __unicode__ = __str__
        