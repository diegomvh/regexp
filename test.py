#!/usr/bin/env python
#-*- encoding: utf-8 -*-
from __future__ import unicode_literals

import re
import unittest

from regexp.snippet import Snippet, Visitor, SnippetHandler
from regexp.string import FormatString

class SnippetTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_parse_snippet(self):
        snippets = [
            '''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>''',
            '''class ${1:ClassName}(${2:object}):
	${3/.+/"""/}${3:docstring for $1}${3/.+/"""\n/}${3/.+/\t/}def __init__(self${4/([^,])?(.*)/(?1:, )/}${4:arg}):
		${5:super($1, self).__init__()}
${4/(\A\s*,\s*\Z)|,?\s*([A-Za-z_][a-zA-Z0-9_]*)\s*(=[^,]*)?(,\s*|$)/(?2:\t\tself.$2 = $2\n)/g}		$0'''
        ]
        for snippet in snippets:
            self.assertEqual(unicode(Snippet(snippet)), snippet)
    
    def test_parse_format_string(self):
        format_strings = [ "${1/class\s+([A-Za-z_][A-Za-z0-9_]*.+?\)?)(\:|$)/$1/g}",
		  "${1/def\s+([A-Za-z_][A-Za-z0-9_]*\()(?:(.{,40}?\))|((.{40}).+?\)))(\:)/$1(?2:$2)(?3:$4…\))/g}"]
        for frmtString in format_strings:
            self.assertEqual(unicode(FormatString(frmtString)), frmtString)

    def test_snippet_holders(self):
        # Build snippet and snippet handler
        snippet = Snippet('''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>''')
        snippetHandler = SnippetHandler()
        snippetHandler.setSnippet(snippet)

        visitor = Visitor()

        # Execute basic
        snippetHandler.execute(visitor)
        self.assertEqual(visitor.output, '<label for=""></label><input type="text" name="" value="" id="">')
        
        # Set content in first holder
        snippetHandler.setContent("Hello world")
        snippetHandler.render(visitor)
        self.assertEqual(visitor.output, '<label for="hello_world">Hello world</label><input type="text" name="hello_world" value="" id="hello_world">')
        
        # Holder navigation
        snippetHandler.nextHolder()
        snippetHandler.nextHolder()
        snippetHandler.setContent(2)
        snippetHandler.nextHolder()
        snippetHandler.setContent("hello_input")
        snippetHandler.nextHolder()
        snippetHandler.nextHolder()
        snippetHandler.nextHolder()
        snippetHandler.setContent("id_hello")
        snippetHandler.render(visitor)
        self.assertEqual(visitor.output, '<label for="hello_world">Hello world</label><input type="hidden" name="hello_input" value="" id="id_hello">')
        
        # Set holder by position
        snippetHandler.setHolder(59)
        snippetHandler.setContent(0)
        snippetHandler.render(visitor)
        self.assertEqual(visitor.output, '<label for="hello_world">Hello world</label><input type="text" name="hello_input" value="" id="id_hello">')

if __name__ == '__main__':
    unittest.main()