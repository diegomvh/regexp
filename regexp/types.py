#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals

import re
from .utils import six
from unicodedata import decomposition

def asciify(string):
    '''"ASCIIfy" a Unicode string by stripping all umlauts, tildes, etc.'''
    def _asciify(char):
        decomp = decomposition(char)
        if decomp:
            return chr(int(decomp.split()[0], 16)) 
        else:
            return char
    return "".join([ _asciify(char) for char in string ])

case_change = { 
    'none': 0, 
    'upper_next': 1,
    'lower_next': 2,
    'upper': 3, 
    'lower': 4 }

case_chars = {
    case_change['none']: '\\E',
    case_change['upper_next']: '\\u',
    case_change['lower_next']: '\\l',
    case_change['upper']: '\\U',
    case_change['lower']: '\\L',
}

case_function = {
    case_change['none']: lambda x : x,
    case_change['upper_next']: lambda x : x[0].upper() + x[1:],
    case_change['lower_next']: lambda x : x[0].lower() + x[1:],
    case_change['upper']: lambda x : x.upper(),
    case_change['lower']: lambda x : x.lower(),
}

transform = { 
    'kNone': 0 << 0, 
    'kUpcase': 1 << 0,
    'kDowncase': 1 << 1,
    'kCapitalize': 1 << 2, 
    'kAsciify': 1 << 3 
}

transform_function = {
    transform['kNone']: lambda x : x,
    transform['kUpcase']: lambda x : x.upper(),
    transform['kDowncase']: lambda x : x.lower(),
    transform['kCapitalize']: lambda x : x.title(),
    transform['kAsciify']: asciify,
}

def escapeCharacters(text, esc):
    for e in esc:
        text = text.replace(e, '\\' + e)            
    return text

#struct variable_t { std::string name; WATCH_LEAKS(parser::variable_t); };
class VariableType(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        if self.name.isdigit():
            return "$%s" % self.name
        else:
            return "${%s}" % self.name

    __unicode__ = __str__    
        
    def replace(self, memodict, holders = None, match = None):
        if self.name.isdigit():
            return match.group(int(self.name))
        return self.name

    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))

#struct variable_condition_t { std::string name; nodes_t if_set, if_not_set; WATCH_LEAKS(parser::variable_condition_t); };
class VariableConditionType(object):
    def __init__(self, name):
        self.name = name
        self.if_set = []
        self.if_not_set = []

    def __str__(self):
        cnd = "(?%s:" % self.name
        for cmps in self.if_set:
            if isinstance(cmps, six.integer_types):
                cnd += case_chars[cmps]
            else:
                cnd += escapeCharacters(six.text_type(cmps), "(:)")
        if self.if_not_set:
            cnd += ":"
            for cmps in self.if_not_set:
                if isinstance(cmps, six.integer_types):
                    cnd += case_chars[cmps]
                else:
                    cnd += escapeCharacters(six.text_type(cmps), "(:)")
        cnd += ")"
        return cnd
    
    __unicode__ = __str__

    def replace(self, memodict, holders = None, match = None):
        group = match.group(int(self.name) - 1)
        print(group)
        nodes = self.if_set if group else self.if_not_set
        text = ""
        case = case_change['none']
        for node in nodes:
            if isinstance(node, six.integer_types):
                case = node
                continue
            value = node.replace(memodict, holders, match)
            # Apply case and append to result
            text += case_function[case](value)
            if case in [case_change['upper_next'], case_change['lower_next']]:
                case = case_change['none']
        return text

    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))

#struct text_t { std::string text; WATCH_LEAKS(parser::text); };
class TextType(object):
    def __init__(self, text):
        self.text = text
    
    def __str__(self):
        return self.text
    
    __unicode__ = __str__
    
    def replace(self, memodict, holders = None, match = None):
        return self.text

    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))
    
#struct placeholder_t { size_t index; nodes_t content; WATCH_LEAKS(parser::placeholder_t); };
class PlaceholderType(object):
    def __init__(self, index):
        self.index = index
        self.content = []
    
    def __str__(self):
        if self.content:
            return "${%s:%s}" % (self.index, "".join([str(node) for node in self.content]))
        else:
            return "$%s" % self.index
    
    __unicode__ = __str__
    
    def replace(self, memodict, holders = None, match = None):
        if self.index in memodict:
            return memodict[self.index]
        elif holders[self.index] != self:
            #Mirror
            return holders[self.index].replace(memodict, holders, match)
        else:
            return "".join([node.replace(memodict, holders, match)
                for node in self.content ])
    
    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))
        
#struct placeholder_choice_t { size_t index; std::vector<nodes_t> choices; WATCH_LEAKS(parser::placeholder_choice_t); };
class PlaceholderChoiceType(object):
    def __init__(self, index):
        self.index = index
        self.choices = []

    def __str__(self):
        return "${%s|%s|}" % (self.index, ",".join([ str(choice) for choice in self.choices]))

    __unicode__ = __str__

    def replace(self, memodict, holders = None, match = None):
        index = self.index in memodict and memodict[self.index] or 0
        return self.choices[index].replace(memodict, holders, match)

    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))
    
#struct placeholder_transform_t { size_t index; regexp::pattern_t pattern; nodes_t format; regexp_options::type options; WATCH_LEAKS(parser::placeholder_transform_t); };
class PlaceholderTransformType(object):
    def __init__(self, index):
        self.index = index
        self.pattern = None
        self.format = []
        self.options = []

    def __str__(self):
        return "${%s/%s/%s/%s}" % (self.index, 
            self.pattern.pattern, 
            "".join([ str(frmt) for frmt in self.format]),
            "".join(self.options))
    
    __unicode__ = __str__
    
    def replace(self, memodict, holders = None, match = None):
        text = ""
        value = holders[self.index].replace(memodict, holders, match)
        match = self.pattern.search(value)
        while match:
            text += "".join([ frmt.replace(memodict, holders, match) for frmt in self.format])
            if 'g' not in self.options:
                break
            match = self.pattern.search(value, match.end())
        return text

    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))

#struct variable_fallback_t { std::string name; nodes_t fallback; WATCH_LEAKS(parser::variable_fallback_t); };
class VariableFallbackType(object):
    def __init__(self, name):
        self.name = name
        self.fallback = []
    
    def replace(self, memodict, holders = None, match = None):
        return self.name
        
    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))

#struct variable_change_t { std::string name; uint8_t change; WATCH_LEAKS(parser::variable_change_t); };
class VariableChangeType(object):
    def __init__(self, name, change):
        self.name = name
        self.change = change

    def __str__(self):
        changes = [""]
        return "${%s:%s}" % (self.name, "/".join(changes))
    
    __unicode__ = __str__

    def replace(self, memodict, holders = None, match = None):
        text = self.name
        for key, function in transform_function.items():
            if self.change & key:
                text = function(text)
        return text
        
    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))

#struct variable_transform_t { std::string name; regexp::pattern_t pattern; nodes_t format; regexp_options::type options; WATCH_LEAKS(parser::variable_transform_t); };
class VariableTransformationType(object):
    def __init__(self, name):
        self.name = name
        self.pattern = None
        self.format = []
        self.options = []
    
    def __str__(self):
        return "${%s/%s/%s/%s}" % (self.name, 
            self.pattern.pattern, 
            "".join([ str(frmt) for frmt in self.format]),
            "".join(self.options))
    
    __unicode__ = __str__
    
    def replace(self, memodict, holders = None, match = None):
        text = ""
        if self.name.isdigit():
            value = holders[self.name].replace(memodict, holders, match)
        else:
            #Recuperarlo del environment
            value = ""
        match = self.pattern.search(value)
        while match:
            text += "".join([ frmt.replace(memodict, holders, match) for frmt in self.format])
            if 'g' not in self.options:
                break
            match = self.pattern.search(value, match.end())
        return text
    
    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))

#struct code_t { std::string code; WATCH_LEAKS(parser::code_t); };
class CodeType(object):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return "`%s`" % (self.code)
    
    __unicode__ = __str__
    
    def replace(self, memodict, holders = None, match = None):
        return self.name

    def render(self, visitor, memodict, holders = None, match = None):
        visitor.insertText(self.replace(memodict, holders, match))
