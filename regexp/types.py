#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals

import re
from .utils import six

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
    'kAsciify': 1 << 3 }

def escapeCharacters(text, esc):
    for e in esc:
        text = text.replace(e, '\\' + e)            
    return text

#struct variable_t { std::string name; WATCH_LEAKS(parser::variable_t); };
class VariableType(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "$" + six.text_type(self.name)
    
    def replace(self, processor, placeholders, match, memo):
        if self.name.isdigit():
            return match.group(int(self.name))
        return self.name

    __unicode__ = __str__

#struct variable_condition_t { std::string name; nodes_t if_set, if_not_set; WATCH_LEAKS(parser::variable_condition_t); };
class VariableConditionType(object):
    def __init__(self, name):
        self.name = name
        self.if_set = []
        self.if_not_set = []

    def replace(self, processor, placeholders, match, memo):
        grps = match.groups()
        index = int(self.name) - 1
        nodes = self.if_set if len(grps) > index and grps[index] is not None else self.if_not_set
        text = ""
        case = case_change['none']
        for node in nodes:
            if isinstance(node, six.integer_types):
                case = node
                continue
            value = node.replace(processor, placeholders, match, memo)
            # Apply case and append to result
            text += case_function[case](value)
            if case in [case_change['upper_next'], case_change['lower_next']]:
                case = case_change['none']
        return text

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

# TODO: Quitar este
class FormatType(object):
    _repl_re = re.compile("\$(?:(\d+)|g<(.+?)>)")
    def __init__(self):
        self.composites = []
    
    @staticmethod
    def prepare_replacement(text):
        def expand(m, template):
            def handle(match):
                numeric, named = match.groups()
                if numeric:
                    return m.group(int(numeric)) or ""
                return m.group(named) or ""
            return FormatType._repl_re.sub(handle, template)
        if '$' in text:
            return lambda m, r = text: expand(m, r)
        else:
            return lambda m, r = text: r

    def apply(self, pattern, text, flags):
        result = []
        match = pattern.search(text)
        if not match: return None
        beginText = text[:match.start()]
        while match:
            nodes = []
            sourceText = text[match.start():match.end()]
            endText = text[match.end():]
            # Translate to conditions
            for composite in self.composites:
                if isinstance(composite, VariableConditionType):
                    nodes.extend(composite.apply(match))
                else:
                    nodes.append(composite)
            # Transform
            case = CASE_NONE
            for value in nodes:
                if isinstance(value, six.string_types):
                    value = pattern.sub(self.prepare_replacement(value), sourceText)
                elif isinstance(value, VariableType):
                    value = match.groups()[value.name - 1]
                elif isinstance(value, six.integer_types):
                    case = value
                    continue
                # Apply case and append to result
                result.append(case_function[case](value))
                if case in [CASE_LOWER_NEXT, CASE_UPPER_NEXT]:
                    case = CASE_NONE
            if 'g' not in flags:
                break
            match = pattern.search(text, match.end())
        try:
            result = "%s%s%s" % (beginText, "".join(result), endText)
        except Exception as ex:
            print(ex, result, six.text_type(self))
        return result 

    def __str__(self):
        frmt = ""
        for cmps in self.composites:
            if isinstance(cmps, six.integer_types):
                frmt += CASE_CHARS[cmps]
            else:
                frmt += six.text_type(cmps)
        return frmt
    
    __unicode__ = __str__

#struct text_t { std::string text; WATCH_LEAKS(parser::text); };
class TextType(object):
    def __init__(self, text):
        self.text = text
    
    def __str__(self):
        return self.text
    
    def replace(self, processor, placeholders, match, memo):
        return self.text

    __unicode__ = __str__
    
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
    
    def replace(self, processor, placeholders, match, memo):
        if self.index in memo:
            return memo[self.index]
        elif placeholders[self.index] != self:
            #Mirror
            return placeholders[self.index].replace(processor, placeholders, match, memo)
        else:
            return "".join([node.replace(processor, placeholders, match, memo)
                for node in self.content ])

    __unicode__ = __str__
    
#struct placeholder_choice_t { size_t index; std::vector<nodes_t> choices; WATCH_LEAKS(parser::placeholder_choice_t); };
class PlaceholderChoiceType(object):
    def __init__(self, index):
        self.index = index
        self.choices = []

    def __str__(self):
        return "${%s:%s}" % (self.index, "|".join(self.choices))
    
    def replace(self, processor, placeholders, match, memo):
        index = self.index in memo and memo[self.index] or 0
        return self.choices[index].replace(processor, placeholders, match, memo)

    __unicode__ = __str__
    
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
    
    def replace(self, processor, placeholders, match, memo):
        text = ""
        value = placeholders[self.index].replace(processor, placeholders, match, memo)
        match = self.pattern.search(value)
        while match:
            text += "".join([ frmt.replace(processor, placeholders, match, memo) for frmt in self.format])
            if 'g' not in self.options:
                break
            match = self.pattern.search(value, match.end())
        return text

    __unicode__ = __str__

#struct variable_fallback_t { std::string name; nodes_t fallback; WATCH_LEAKS(parser::variable_fallback_t); };
class VariableFallbackType(object):
    def __init__(self, name):
        self.name = name
        self.fallback = []
    
    def replace(self, processor, placeholders, match, memo):
        return self.name
        
#struct variable_change_t { std::string name; uint8_t change; WATCH_LEAKS(parser::variable_change_t); };
class VariableChangeType(object):
    def __init__(self, name, change):
        self.name = name
        self.change = change
    
    def __str__(self):
        changes = [""]
        return "${%s:%s}" % (self.name, "/".join(changes))
    
    def replace(self, processor, placeholders, match, memo):
        return self.name
        
    __unicode__ = __str__
    
#struct variable_transform_t { std::string name; regexp::pattern_t pattern; nodes_t format; regexp_options::type options; WATCH_LEAKS(parser::variable_transform_t); };
class VariableTransformationType(object):
    def __init__(self, name):
        self.name = name
        self.pattern = None
        # TODO: Sacar este format se tiene que resolver aca
        self.format = []
        self.options = []
        
    def transform(self, text):
        return self.format.apply(self.pattern, text, self.options)

    def __str__(self):
        return "${%s/%s/%s/%s}" % (self.name, 
            self.pattern.pattern, 
            "".join([ str(frmt) for frmt in self.format]),
            "".join(self.options))
    
    def replace(self, processor, placeholders, match, memo):
        text = ""
        if self.name.isdigit():
            value = placeholders[self.name].replace(processor, placeholders, match, memo)
        else:
            #Recuperarlo del environment
            value = ""
        match = self.pattern.search(value)
        while match:
            text += "".join([ frmt.replace(processor, placeholders, match, memo) for frmt in self.format])
            if 'g' not in self.options:
                break
            match = self.pattern.search(value, match.end())
        return text
    
    __unicode__ = __str__

#struct code_t { std::string code; WATCH_LEAKS(parser::code_t); };
class CodeType(object):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return "`%s`" % (self.code)
    
    def replace(self, processor, placeholders, match, memo):
        return self.name

    __unicode__ = __str__