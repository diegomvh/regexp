#!/usr/bin/env python

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
            self.assertEqual(str(Snippet(snippet)), snippet)
    
    def test_parse_format_string(self):
        string = FormatString("storage.type.class.${1:/downcase}")
        print(string.replace({}))

    def test_snippet_holders(self):
        visitor = Visitor()
        snippetHandler = SnippetHandler()
        snippetHandler.setSnippet(Snippet('''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>'''))
        snippetHandler.execute(visitor)
        print(visitor.output)
        snippetHandler.setContent("hola mundo")
        snippetHandler.render(visitor)
        print(visitor.output)
        snippetHandler.nextHolder()
        snippetHandler.setContent("id_cacho")
        snippetHandler.render(visitor)
        print(visitor.output)
        snippetHandler.nextHolder()
        snippetHandler.setContent(2)
        snippetHandler.nextHolder()
        snippetHandler.setContent("my_name")
        snippetHandler.nextHolder()
        snippetHandler.setContent("hola value")
        snippetHandler.nextHolder()
        snippetHandler.nextHolder()
        snippetHandler.setContent("id_input")
        snippetHandler.render(visitor)
        print(visitor.output)
        snippetHandler.nextHolder()
        snippetHandler.setHolder(15)
        snippetHandler.setContent("otro_cacho")
        snippetHandler.render(visitor)
        print(visitor.output)

if __name__ == '__main__':
    unittest.main()